from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError,transaction
from .models import Device
class DeviceTests(TestCase):
 def setUp(self):
  self.a=Device.objects.create(name='Холод камера',serial='V03-A'); Device.objects.create(name='Холод шлюз',serial='V03-B'); Device.objects.create(name='Склад',serial='V03-C')
 def test_pages_search(self):
  self.assertEqual(self.client.get('/').status_code,200); self.assertEqual(self.client.get(f'/devices/{self.a.pk}/').status_code,200); self.assertEqual(self.client.get('/devices/999/').status_code,404); self.assertEqual(self.client.post('/').status_code,405)
  before=Device.objects.count(); r=self.client.get('/',{'q':'Холод'}); self.assertEqual(len(r.context['devices']),2); self.assertEqual(len(self.client.get('/',{'q':''}).context['devices']),3); self.assertEqual(len(self.client.get('/',{'q':'неіснуючий-зразок'}).context['devices']),0); self.assertEqual(Device.objects.count(),before)
 def test_empty(self):
  Device.objects.all().delete(); self.assertContains(self.client.get('/'),'Пристроїв немає')
 def test_duplicate(self):
  with self.assertRaises(IntegrityError), transaction.atomic(): Device.objects.create(name='Дубль',serial=self.a.serial)
 def test_admin_rights(self):
  u=get_user_model().objects.create_user(username='regular',password='local-test'); self.client.force_login(u); self.assertEqual(self.client.get('/admin/').status_code,302)
  admin=get_user_model().objects.create_superuser(username='admin',password='local-test'); self.client.force_login(admin)
  r=self.client.post('/admin/monitoring/device/add/',{'name':'Тестовий','serial':'ADMIN-DEMO'}); self.assertEqual(r.status_code,302); self.assertTrue(Device.objects.filter(serial='ADMIN-DEMO').exists())

from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db.models import Avg,Count
from django.db.models.deletion import ProtectedError
from django.utils import timezone
from .models import Measurement,Passport,Tag
class RelationsTests(TestCase):
 def test_integrity_and_queries(self):
  d=Device.objects.create(name='Холод камера',serial='C1'); empty=Device.objects.create(name='Склад',serial='C2'); tag=Tag.objects.create(name='Холод'); d.tags.add(tag); Passport.objects.create(device=empty,location='Склад')
  a=Measurement.objects.create(device=d,temperature=Decimal('-5.00'),measured_at=timezone.now()); Measurement.objects.create(device=d,temperature=Decimal('5.00'),measured_at=timezone.now())
  self.assertEqual(Measurement.objects.aggregate(mean=Avg('temperature'))['mean'],Decimal('0')); self.assertEqual(Measurement.objects.filter(temperature__gt=0).count(),1)
  self.assertEqual(Device.objects.filter(tags__name='Холод').distinct().count(),1); self.assertIsNone(Device.objects.annotate(mean=Avg('measurements__temperature')).get(pk=empty.pk).mean)
  a.temperature=Decimal('-4.00'); a.save(); a.refresh_from_db(); self.assertEqual(a.temperature,Decimal('-4.00')); a.delete(); self.assertEqual(d.measurements.count(),1)
  with self.assertRaises(ProtectedError): d.delete()
  self.assertEqual(d.measurements.count(),1); empty.delete(); self.assertFalse(Passport.objects.exists())
 def test_validation_and_db_constraint(self):
  d=Device.objects.create(name='Холод',serial='C1')
  for v in ('-80','150'): Measurement(device=d,temperature=Decimal(v)).full_clean()
  with self.assertRaises(ValidationError): Measurement(device=d,temperature=Decimal('151')).full_clean()
  with self.assertRaises(IntegrityError),transaction.atomic(): Measurement.objects.create(device=d,temperature=Decimal('151'))
