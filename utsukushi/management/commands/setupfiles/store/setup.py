from django.contrib.auth.models import Group, User
from . import data

def start(cmd):
    cmd.stdout.write(cmd.style.SUCCESS('Creating role: administration'), ending='\n')
    administration, created = Group.objects.get_or_create(name='administration')
    if not created:
        cmd.stdout.write(cmd.style.WARNING('Role: administration already exists'), ending='\n')

    cmd.stdout.write(cmd.style.SUCCESS('Creating role: discount'), ending='\n')
    discount, created = Group.objects.get_or_create(name='discount')
    if not created:
        cmd.stdout.write(cmd.style.WARNING('Role: discount already exists'), ending='\n')

    cmd.stdout.write(cmd.style.SUCCESS('Creating role: order'), ending='\n')
    order, created = Group.objects.get_or_create(name='order')
    if not created:
        cmd.stdout.write(cmd.style.WARNING('Role: order already exists'), ending='\n')

    cmd.stdout.write(cmd.style.SUCCESS( 'Creating user: admin'), ending='\n')
    user, created = User.objects.get_or_create(username='admin')
    if created:
        user.email = 'admin@webstore.user'
        user.set_password('admin1')
        user.groups.add(administration)
        user.is_staff = True
        user.save()
    else:
        cmd.stdout.write(cmd.style.WARNING('User: admin already exists'), ending='\n')

    cmd.stdout.write(cmd.style.SUCCESS( 'Creating user: discount'), ending='\n')
    user, created = User.objects.get_or_create(username='discount')
    if created:
        user.email = 'discount@webstore.user'
        user.set_password('admin1')
        user.groups.add(discount)
        user.is_staff = True
        user.save()
    else:
        cmd.stdout.write(cmd.style.WARNING('User: discount already exists'), ending='\n')

    cmd.stdout.write(cmd.style.SUCCESS('Creating user: stockroom'), ending='\n')
    user, created = User.objects.get_or_create(username='stockroom')
    
    if created:
        user.email = 'stockroom@webstore.user'
        user.set_password('admin1')
        user.first_name = 'Stockroom'
        user.last_name = 'User'
        user.groups.add(order)
        user.is_staff = True
        user.save()

    else:
        cmd.stdout.write(cmd.style.WARNING('User: stockroom already exists'), ending='\n')

    cmd.stdout.write(cmd.style.SUCCESS('Creating superuser: super'), ending='\n')
    user, created = User.objects.get_or_create(username='super')
    if created:
        user.set_password('super1')
        user.force_password_change = False
        user.is_superuser = True
        user.is_staff = True
        user.save()

    else:
        cmd.stdout.write(cmd.style.WARNING('User: super already exists'), ending='\n')

    ################ Add other users e.g practitioners, nurses here ############################################
    


    ##########################################################################################################
    cmd.stdout.write(cmd.style.SUCCESS('SETUP WEBSTORE DATA'), ending='\n')
    data.inject(cmd)
