from django.db.models import Avg,Count
from django.shortcuts import get_object_or_404,render
from django.views.decorators.http import require_safe
from .models import Device
@require_safe
def index(request):
 q=request.GET.get('q','').strip(); devices=Device.objects.annotate(n=Count('measurements'),mean=Avg('measurements__temperature')).order_by('serial')
 if q: devices=devices.filter(name__icontains=q)
 return render(request,'monitoring/index.html',{'devices':devices,'q':q})
@require_safe
def device_detail(request,pk):
 device=get_object_or_404(Device,pk=pk)
 return render(request,'monitoring/detail.html',{'device':device,'measurements':device.measurements.order_by('-measured_at','-pk')})
