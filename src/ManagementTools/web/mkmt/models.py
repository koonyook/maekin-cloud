from django.db import models
from django.db import models
from django import forms
from django.contrib.auth.models import User
from django.forms.models import modelformset_factory
from django.forms import ModelForm
from django.db.models.signals import post_save
# Create your models here.


class Admin_mkmt(models.Model):
	user = models.ForeignKey(User)
	def __unicode__(self):
		return self.user.username
		
class GuestIP(models.Model):
	IP =  models.CharField(max_length=200)
	def __unicode__(self):
		return self.IP
class DnsIP(models.Model):
	dnsAddressIP = models.CharField(max_length=200)
	def __unicode__(self):
		return self.dnsAddressIP

class Cloud(models.Model):
	UUID =  models.CharField(max_length=200,unique=True)
	name =  models.CharField(max_length=200,unique=True)	
	default = models.CharField(max_length=200,unique=True)
	middleIP = models.CharField(max_length=200,unique=True)
	GuestPool = models.ManyToManyField(GuestIP,blank=True)
	DNSPool = models.ManyToManyField(DnsIP,blank=True)
	network = models.CharField(max_length=200)
	subnet = models.CharField(max_length=200)
	mode = models.PositiveIntegerField()
	#lastVMImageID = models.PositiveIntegerField(null=True)
	def __unicode__(self):
		return self.middleIP

class Template(models.Model):
	templateID = models.PositiveIntegerField(unique=True)
	description = models.CharField(max_length=200)
	OS = models.CharField(max_length=200)
	ostype = models.CharField(max_length=200)
	minMem = models.PositiveIntegerField()
	maxMem = models.PositiveIntegerField()
	def __unicode__(self):
		return self.OS
class VI(models.Model):
	ownerCloud = models.ForeignKey(Cloud)
	owner = models.ForeignKey(User)
	name = models.CharField(max_length=200,unique=True)
	template = models.ManyToManyField(Template,blank=True)
	quotaIP = models.PositiveIntegerField()
	quotaVCPU = models.PositiveIntegerField(null=True)
	quotaRAM = models.PositiveIntegerField(null=True)
	usedIP = models.PositiveIntegerField(default=0)
	usedVCPU = models.PositiveIntegerField(default=0)
	usedRAM = models.PositiveIntegerField(default=0)
	def __unicode__(self):
		return self.name
class VIrequest(models.Model):
	ownerCloud = models.ForeignKey(Cloud)
	owner = models.ForeignKey(User)
	name = models.CharField(max_length=200,unique=True)
	adminGroup = models.ManyToManyField(User,blank=True,related_name='admin_group')
	template = models.ManyToManyField(Template,blank=True)
	quotaIP = models.PositiveIntegerField()
	quotaVCPU = models.PositiveIntegerField(null=True)
	quotaRAM = models.PositiveIntegerField(null=True)
	waiting = models.BooleanField(default=True)
	accept = models.BooleanField(default=False)
class VM(models.Model):
	imageID = models.PositiveIntegerField(unique=True)
	name = models.CharField(max_length=200)
	IP = models.CharField(max_length=200)
	template = models.ForeignKey(Template)
	ssh = models.BooleanField()
	remote = models.BooleanField()
	ownerVI = models.ForeignKey(VI)
	vCPU = models.PositiveIntegerField()
	memory = models.PositiveIntegerField()
	def __unicode__(self):
		return self.name
class Role(models.Model):
	name = models.CharField(max_length=200,unique=True)
	ownerVI = models.ForeignKey(VI)
	roleEdit = models.BooleanField()
	userAdd = models.BooleanField()
	userRemove = models.BooleanField()
	vmControl = models.BooleanField()
	vmCreate = models.BooleanField()
	vmDelete = models.BooleanField()
	templateAdd = models.BooleanField()
	templateRemove = models.BooleanField()
	user = models.ManyToManyField(User,blank=True)
	def __unicode__(self):
		return self.name
class Spec(models.Model):
	CPU = models.CharField(max_length=200)
	HDD = models.CharField(max_length=200)
	RAM = models.CharField(max_length=200)
	ownerVM = models.ForeignKey(VM)
class ResourceLeft(models.Model):
	CPU = models.CharField(max_length=200)
	HDD = models.CharField(max_length=200)
	RAM = models.CharField(max_length=200)	
	ownerVM = models.ForeignKey(VM)	
class VMLog(models.Model):
	username = models.CharField(max_length=200)
	action = models.CharField(max_length=200)
	taskID = models.PositiveIntegerField(null=True)
	vmImageID = models.PositiveIntegerField(null=True)
	vmName = models.CharField(max_length=200,null=True)
	viID = models.PositiveIntegerField(null=True)
	startTime = models.CharField(max_length=200,null=True)
	finishTime = models.CharField(max_length=200,null=True)
	status = models.CharField(max_length=20,default="queued")
	error = models.NullBooleanField(null=True)
	finishMessage =  models.CharField(max_length=1000,null=True)
	def __unicode__(self):
		return self.status+"__"+self.username+" : "+self.action+" : "+str(self.vmImageID)
class HostLog(models.Model):
	username = models.CharField(max_length=200)
	action = models.CharField(max_length=200)
	taskID = models.PositiveIntegerField(null=True)
	hostID = models.PositiveIntegerField(null=True)
	startTime = models.CharField(max_length=200,null=True)
	finishTime = models.CharField(max_length=200,null=True)
	status = models.CharField(max_length=20,default="queued")
	error = models.NullBooleanField(null=True)
	finishMessage =  models.CharField(max_length=1000,null=True)
	def __unicode__(self):
		return self.status+"__"+self.username+" : "+self.action+" : "+str(self.hostID)
class UseLog(models.Model):
	userID  = models.ForeignKey(User)
	action = models.CharField(max_length=200)
class Storage(models.Model):
	nfsIP = models.CharField(max_length=200)
	size = models.PositiveIntegerField()
	vmID = models.ForeignKey(VM)
class currentCloud(models.Model):
	cloud = models.ForeignKey(Cloud)
	def __unicode__(self):
		return self.cloud.name
##models for web tools

class Host(models.Model):
	MAC = models.CharField(max_length=200)
	IP =  models.CharField(max_length=200)
	hostName =  models.CharField(max_length=200)
	owner = models.ForeignKey(Cloud)
	def __unicode__(self):
		return self.hostName


class RegisForm(ModelForm):
	class Meta:
		model = User
		fields = ('username','password','email')
class ManageProfileForm(ModelForm):
	class Meta:
		model = User
		fields = ('password','email')
class newVIForm(ModelForm):
	class Meta:
		model = VI
VIForm = modelformset_factory(VI)
