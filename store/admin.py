import csv
import io
import re
from decimal import Decimal

from django import forms
from django.contrib import admin, messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path
from django.utils import timezone
from django.utils.text import slugify

from .models import Brand, Category, CurrencyRate, Product, ProductImage

IMAGE_COLUMN_KEYS = (
    'image_url',
    'image_src',
    'image',
    'image_link',
    'img_url',
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'logo')
    search_fields = ('name',)


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class ProductAdminForm(forms.ModelForm):
    additional_images = forms.ImageField(
        required=False,
        widget=MultipleFileInput(attrs={'multiple': True}),
        help_text='Optional: upload one or more additional images.',
    )

    class Meta:
        model = Product
        fields = '__all__'


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'sort_order')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ('name', 'sku', 'brand', 'category', 'price', 'item_stock', 'in_stock', 'updated_at')
    search_fields = ('name', 'sku')
    list_filter = ('brand', 'category', 'updated_at')
    change_list_template = 'admin/store/product_changelist.html'
    readonly_fields = ('in_stock', 'subtract_from')
    inlines = [ProductImageInline]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-csv/', self.admin_site.admin_view(self.import_csv), name='store_product_import'),
        ]
        return custom_urls + urls

    def response_change(self, request, obj):
        if '_update_stock' in request.POST:
            obj.item_stock = _parse_int(request.POST.get('item_stock'))
            obj.subtract_from = timezone.now()
            obj.save(update_fields=['item_stock', 'subtract_from'])
            self.message_user(request, f'Updated stock baseline for "{obj.name}".', level=messages.SUCCESS)
            return redirect(request.path)
        return super().response_change(request, obj)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        for uploaded in request.FILES.getlist('additional_images'):
            ProductImage.objects.create(product=form.instance, image=uploaded)

    def import_csv(self, request):
        if request.method == 'POST':
            form = ProductImportForm(request.POST, request.FILES)
            if form.is_valid():
                created, updated, has_image_column = self._handle_csv(
                    form.cleaned_data['csv_file'],
                    form.cleaned_data.get('delimiter') or None,
                )
                messages.success(
                    request,
                    f"Import complete. Created {created} products, updated {updated} products.",
                )
                if not has_image_column:
                    messages.warning(
                        request,
                        "Import completed, but no image column was detected. "
                        f"Expected one of: {', '.join(IMAGE_COLUMN_KEYS)}.",
                    )
                return redirect('..')
        else:
            form = ProductImportForm()

        context = {
            **self.admin_site.each_context(request),
            'title': 'Import products from CSV',
            'form': form,
        }
        return TemplateResponse(request, 'admin/store/product_import.html', context)

    def _handle_csv(self, uploaded_file, delimiter_override=None):
        raw = uploaded_file.read()
        text, _ = _decode_csv(raw)
        sample = text[:2048]
        header_line = text.splitlines()[0] if text else ''
        delimiter = delimiter_override or _detect_delimiter(header_line)
        if delimiter_override:
            dialect = csv.excel
            dialect.delimiter = delimiter
            text = _merge_multiline_rows(text, delimiter)
        else:
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=[',', ';', '\t', '|'])
                delimiter = dialect.delimiter or delimiter
            except csv.Error:
                dialect = csv.excel
                dialect.delimiter = delimiter
        reader = csv.DictReader(io.StringIO(text), dialect=dialect, skipinitialspace=True)
        fieldnames = reader.fieldnames or []
        normalized_fieldnames = {
            _normalize_header_key(fieldname)
            for fieldname in fieldnames
            if fieldname is not None
        }
        has_image_column = any(key in normalized_fieldnames for key in IMAGE_COLUMN_KEYS)
        created = 0
        updated = 0

        for row in reader:
            if None in row and row.get(None):
                extra = row.get(None)
                if isinstance(extra, list) and extra:
                    if row.get('description') is not None:
                        row['description'] = f"{row.get('description','')},{','.join(extra)}"
            clean_row = _normalize_row(row)
            raw_name = (clean_row.get('name') or '').strip()
            brand, name = _split_brand_name(raw_name)
            if not name:
                continue

            defaults = _row_to_defaults(clean_row)
            if brand:
                defaults['brand'] = brand
            product = Product.objects.filter(name__iexact=name).first()
            if product:
                for key, value in defaults.items():
                    setattr(product, key, value)
                product.save()
                updated += 1
                continue

            sku = _generate_sku(name)
            product = Product.objects.create(name=name, sku=sku, **defaults)
            created += 1

        return created, updated, has_image_column


class ProductImportForm(forms.Form):
    csv_file = forms.FileField()
    delimiter = forms.ChoiceField(
        choices=[(',', 'Comma (,)'), (';', 'Semicolon (;)'), ('\t', 'Tab')],
        required=False,
    )


@admin.register(CurrencyRate)
class CurrencyRateAdmin(admin.ModelAdmin):
    list_display = ('code', 'symbol', 'rate', 'updated_at')
    search_fields = ('code',)


def _decode_csv(raw: bytes):
    for encoding in ('utf-8-sig', 'cp949', 'euc-kr', 'latin-1'):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return raw.decode('latin-1', errors='replace'), 'latin-1'


_number_re = re.compile(r'[-+]?(?:\d+\.?\d*|\d*\.\d+)')


def _parse_decimal(value):
    if value is None:
        return None
    value = str(value).strip()
    if not value:
        return None
    match = _number_re.search(value.replace(',', ''))
    if not match:
        return None
    try:
        return Decimal(match.group(0))
    except Exception:
        return None


def _parse_int(value):
    if value is None:
        return None
    value = str(value).strip()
    if not value:
        return None
    match = _number_re.search(value.replace(',', ''))
    if not match:
        return None
    try:
        return int(Decimal(match.group(0)))
    except Exception:
        return None


def _generate_sku(name: str) -> str:
    base = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-') or 'item'
    sku = base
    counter = 1
    while Product.objects.filter(sku=sku).exists():
        counter += 1
        sku = f"{base}-{counter}"
    return sku


def _split_brand_name(raw_name: str):
    if not raw_name:
        return None, ''
    if '-' not in raw_name:
        return None, raw_name.strip()
    brand_part, name_part = raw_name.split('-', 1)
    brand_name = brand_part.strip()
    product_name = name_part.strip().title()
    if not product_name:
        return None, raw_name.strip()
    brand = None
    if brand_name:
        brand, _ = Brand.objects.get_or_create(name=brand_name)
    return brand, product_name


def _row_to_defaults(row):
    unit_price = _parse_decimal(row.get('unit_price'))
    total_price = _parse_decimal(row.get('total_price'))
    sales_price_round = _parse_decimal(row.get('sales_price_round'))
    weight_raw = row.get('weight') or row.get('unit_weight')
    weight_value = _parse_decimal(weight_raw)
    weight_unit = _parse_unit(weight_raw)
    image_raw = next(
        (
            row.get(key)
            for key in (
                'image_url',
                'image_src',
                'image',
                'image_link',
                'img_url',
            )
            if row.get(key)
        ),
        None,
    )
    image_value = _normalize_image_path(image_raw)
    description = (row.get('description') or '').strip()
    category = _get_or_create_category(row.get('category'))

    return {
        'description': description,
        'category': category,
        'unit_price': unit_price,
        'weight': weight_value,
        'unit_weight': weight_unit or '',
        'quantity': _parse_int(row.get('quantity')),
        'total_price': total_price,
        'calculated_weight_price': _parse_decimal(row.get('calculated_weight_price')),
        'sales_price_calc': _parse_decimal(row.get('sales_price_calc')),
        'sales_price_round': sales_price_round,
        'item_stock': _parse_int(row.get('item_stock')),
        'total_gifts': _parse_int(row.get('total_gifts')),
        'image_url': image_value or '',
        'price': sales_price_round or unit_price or total_price or Decimal('0.00'),
    }


def _parse_unit(value):
    if value is None:
        return None
    value = str(value).strip()
    if not value:
        return None
    match = re.search(r'[a-zA-Z]+', value)
    return match.group(0).lower() if match else None


def _normalize_image_path(value):
    if value is None:
        return None
    value = str(value).strip()
    if not value:
        return None
    if value.startswith(('img/products/', '/img/products/')):
        return f"/{value.lstrip('/')}"
    if value.startswith('http://') or value.startswith('https://'):
        return value
    return f"/img/products/{value.lstrip('/')}"


def _get_or_create_category(value):
    if value is None:
        return None
    name = str(value).strip()
    if not name:
        return None
    slug = slugify(name)[:140]
    category, _ = Category.objects.get_or_create(slug=slug, defaults={'name': name})
    if category.name != name:
        category.name = name
        category.save(update_fields=['name'])
    return category


def _normalize_row(row):
    cleaned = {}
    for key, value in row.items():
        if key is None:
            continue
        normalized = _normalize_header_key(key)
        if isinstance(value, str):
            value = value.strip()
        cleaned[normalized] = value
    return cleaned


def _normalize_header_key(key):
    normalized = str(key).strip().lower()
    return re.sub(r'[^a-z0-9]+', '_', normalized).strip('_')


def _detect_delimiter(header_line: str) -> str:
    candidates = [',', ';', '\t', '|']
    counts = {c: header_line.count(c) for c in candidates}
    return max(counts, key=counts.get) if counts else ','


def _merge_multiline_rows(text: str, delimiter: str) -> str:
    lines = text.splitlines()
    if not lines:
        return text
    header = lines[0]
    expected_fields = len(header.split(delimiter))
    merged_lines = [header]
    buffer = ''
    for line in lines[1:]:
        if not buffer:
            buffer = line
        else:
            buffer = f"{buffer}\n{line}"
        if buffer.count(delimiter) >= expected_fields - 1:
            merged_lines.append(buffer)
            buffer = ''
    if buffer:
        merged_lines.append(buffer)
    return "\n".join(merged_lines)
