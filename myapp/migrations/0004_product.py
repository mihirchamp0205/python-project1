# Generated by Django 4.1.3 on 2022-11-14 11:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0003_user_profile_pic'),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_company', models.CharField(max_length=100)),
                ('product_model', models.CharField(max_length=100)),
                ('product_desc', models.TextField()),
                ('product_price', models.IntegerField()),
                ('product_image', models.ImageField(upload_to='product_image/')),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='myapp.user')),
            ],
        ),
    ]
