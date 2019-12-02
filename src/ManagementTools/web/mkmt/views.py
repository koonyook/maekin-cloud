from func import *
################################################################
## Global Variable for view
################################################################
#global allvi
#allvi = list(VI.objects.all())
# def refreshVI(request):
	#global allvi
	# vi_hold = list(VI.objects.filter(Q(adminGroup=request.user))) + list(VI.objects.filter(Q(userGroup=request.user)))
# cloudURL = ''
# vi_hold = []
# alltemplatelist = {}
################################################################
## function for view
################################################################
def init(request):
	if initCloud():
		base_template= 'base_guest.html'
		error_middle = ''
		middleIP = ''
	else:
		return redirect('/')
		# if request.user.is_anonymous():
			# return redirect('/')
		# elif isCloudAdmin(request.user):
			# base_template = 'base_admin.html'
			# middleIP = getMiddlewareIP()
			# error_middle = ''
		# else:
			# return redirect('/')
	return render_to_response('init.html',{'base_template':base_template,'error_middle':error_middle,'middleIP':middleIP},context_instance=RequestContext(request))
def cloud(request):
	if not isCloudAdmin(request.user):
		return redirect('/')
	curCloud = getCurrentCloud()
	cloudMode = curCloud.mode
	middleIP = getMiddlewareIP()
	guestPoollist = getCurrentGuestPoolNetworkGroup()
	return render_to_response('cloud.html',{'middleIP':middleIP,'cloudMode':cloudMode,'cloud':curCloud,'guestPoollist':guestPoollist},context_instance=RequestContext(request))
def editCloud(request):
	if isCloudAdmin(request.user):
		changeMid = request.POST['changeMid']
		midIP  = request.POST['middlewareIP']
		autoMode = request.POST['autoMode']
		text = cloud_rURL("/cloud/setAutoMode?mode="+autoMode)
		if text != '':
			curCloud = getCurrentCloud()
			curCloud.middleIP = midIP
			curCloud.save()
			updatestatus = updateCloudInfo()
			if updatestatus != "clear":
				return HttpResponse(updatestatus)
		return HttpResponse('clear')
	else:
		return HttpResponse("Error don't have permission")
def index(request):
	if Admin_mkmt.objects.all().count() == 0:
		return redirect('/init')
	if request.user.is_authenticated():	
		return redirect('/vi')
	else:
		return render_to_response('index.html',{},context_instance=RequestContext(request))
def xml(request):
	if request.method == 'POST':
		input = request.POST
		midIP = input['MiddlewareIP']
		cloud_info = getCloudInfo(midIP)
		if type(cloud_info) == str:
			base_template= 'base_guest.html'
			error_middle = cloud_info
			return render_to_response('init.html',{'base_template':base_template,'error_middle':error_middle,'def_adminname':input['AdminName'],'def_adminemail':input['AdminEmail'],
			'def_defaultVIName':input['globalCloudName'],'def_adminpass':input['AdminPass']},context_instance=RequestContext(request))
		else:
			if get_or_none(User,username=input['AdminName']) != None:
				return render_to_response('init.html',{'error_admin':'Please use another adminname','base_template':base_template,'def_adminname':input['AdminName'],'def_adminemail':input['AdminEmail'],
			'def_defaultVIName':input['globalCloudName'],'def_adminpass':input['AdminPass']},context_instance=RequestContext(request))
			if (len(Cloud.objects.filter(middleIP=midIP))== 0):
			#if (len(Cloud.objects.filter(UUID=input['UUID']))== 0):
				#writeXML(input)
				cloudobj = storeCloudStartup(midIP,cloud_info,True)
				currcloud =  currentCloud.objects.create(cloud=cloudobj)
				storeAdminCloudTmp(input)
				### for random password
				#tmpadminpass = storeAdminCloudTmp(input)
				#return render_to_response('initComplete.html',{ 'input' : input,'password' :tmpadminpass },context_instance=RequestContext(request))
				###
				user = authenticate(username=input['AdminName'], password=input['AdminPass'])
				login(request,user)
				defaultVI = createVI(input['globalCloudName'],user,[user.id],[],len(currcloud.cloud.GuestPool.all()),None,None,id=0)
				for template in getTemplate():
					defaultVI.template.add(Template.objects.get(templateID=template['id']))
			else:
				cloudobj = storeCloudStartup(midIP,cloud_info,False)
				currcloud = currentCloud.objects.get(id=1)
				currcloud.cloud = cloudobj
				currcloud.save
			return redirect('/home')
	else:
		return redirect('/')
	#return render_to_response('initComplete.html',{ },context_instance=RequestContext(request))
	#else:
	#	return HttpResponse(check)
def login_view(request):
	name = request.POST['username']
	password = request.POST['password']
	user = authenticate(username=request.POST['username'], password= request.POST['password'])
	if user is not None:
		if user.is_active:
			login(request, user)
			# Redirect to a success page.
			return redirect('/home')
		else:
			# Return a 'disabled account' error message
			return render_to_response('index.html',{'error':"Your username and password didn't match.",'filled_username':name},context_instance=RequestContext(request))
	else:
		# Return an 'invalid login' error message.
		return render_to_response('index.html',{'error':"Your username and password didn't match.",'filled_username':name},context_instance=RequestContext(request))
	
	# if not User.objects.filter(username=request.POST['username']).count() == 0:
		# u = User.objects.get(username=request.POST['username'])
		# if u.password == request.POST['password']:
			# request.session['user_id'] = u.id
			#return HttpResponse("You're logged in.")
			# 
		# else:
			# return render_to_response('base_guest.html',{'error':"Your username and password didn't match."},context_instance=RequestContext(request))
	# else:
		# return render_to_response('base_guest.html',{'error':"no User name : "+request.POST['username']},context_instance=RequestContext(request))
def home(request):
	return redirect('/vi')
	cloudURL = Cloud.objects.get(UUID=0).middleIP
	if not request.user.is_authenticated():	
	#if not request.session.has_key('user_id'):
		return render_to_response('base_guest.html',{},context_instance=RequestContext(request))
	return render_to_response('base_user.html',{},context_instance=RequestContext(request))
def logout_view(request):
	logout(request)
	return redirect('/')
	# try:
		# name = str(User.objects.get(id=request.session['user_id']))
		# del request.session['user_id']
		# request.session.flush()
		# return render_to_response('base_guest.html',{'error':'log out from '+name},context_instance=RequestContext(request))
	# except KeyError:
		# pass
		# return render_to_response('base_guest.html',{'error':'You are not login'},context_instance=RequestContext(request))
def regis(request):
	# if request.user.is_authenticated():
		# base_template = 'base_user.html'
	# else:
	base_template= 'base.html'
	regis_complete = False
	error_username = ''
	error_email = ''
	input_username = ''
	input_password = ''
	input_email = ''
	if request.method == 'POST':
		clear = True
		input_username = request.POST['username']
		input_password = request.POST['password']
		input_email = request.POST['email']
		if input_username == '' or input_password == '' or input_email == '':
			clear = False
			error_username = 'Please fill required field'
		if len(User.objects.filter(username=input_username)) > 0:
			clear = False
			error_username = 'Username '+input_username+' is already used'
		if len(User.objects.filter(email=input_email)) > 0:
			clear = False
			error_email = 'Email '+input_email+' is already used'
		if clear:
			createUser(input_username, input_email,input_password)
			regis_complete = True
		# form = RegisForm(request.POST)
		# if form.is_valid():
			# createUser(request.POST['username'], request.POST['email'], request.POST['password'])
			# return redirect('/')
	# else:
		# form = RegisForm()
	args = {'input_username':input_username,'input_password':input_password,'input_email':input_email,'base_template':base_template,'error_username':error_username,'error_email':error_email,'regis_complete':regis_complete}
	return render_to_response('regis.html',args,context_instance=RequestContext(request))
def manvi(request):
	if  not request.user.is_authenticated:	
		return redirect('/')
	if request.user.is_anonymous():	
		return redirect('/')
	vi_id = 0
	if request.method == 'POST':
		vi_id = request.POST['vi_id']
	allActiveUser = User.objects.filter(is_superuser=False)
	vi_hold =[]
	for user_role in Role.objects.filter(user=User.objects.filter(username=request.user)):
		vi_hold.append({'vi':user_role.ownerVI})
	vm_raw_list = getVMinfo()
	getTemplate()
	templatelist = []
	for vi in vi_hold:
		vi['vmlist'] = []
		vmlist = VM.objects.filter(ownerVI=vi['vi'])
		for vm_data in vmlist:
			getvm = False
			for vm_raw in vm_raw_list:
				if vm_data.imageID == int(vm_raw['imageID']):
					getvm = True
					vi['vmlist'].append(vm_raw)
					vm_raw_list.remove(vm_raw)
				if getvm:
					break
			if not getvm:
				#VM.objects.get(imageID=vm_data.imageID).delete()
				
				lostVM(vm_data.imageID)
				#vi['vmlist'].append(vm_data)
		vi['template'] = vi['vi'].template.all()
		vi['roleList'] = []
		vi['userGroup'] = []
		vi['userRole'] = Role.objects.get(ownerVI=vi['vi'],user=request.user)
		for role in Role.objects.filter(ownerVI=vi['vi']):
			vi['roleList'].append({'role':role,'usergroup':role.user.all()})
			vi['userGroup'] = list(chain(vi['userGroup'],role.user.all()))
		vi['adminGroup'] = Role.objects.get(ownerVI=vi['vi'],roleEdit=True).user.all()
		for tem in vi['template']:
			if not templatelist.__contains__(tem):
				templatelist.append(tem)
		vi['log'] = VMLog.objects.filter(viID=vi['vi'].id)
		vi['ratioIP'] = float(vi['vi'].usedIP)/float(vi['vi'].quotaIP)*100
		if vi['vi'].id == 0:
			vi['ratiovCPU'] = 0
			vi['ratioRAM'] = 0 
		else:
			vi['ratiovCPU'] =  float(vi['vi'].usedVCPU)/ float(vi['vi'].quotaVCPU )*100
			vi['ratioRAM'] =  float(vi['vi'].usedRAM)/ float(vi['vi'].quotaRAM )*100
		#a = 1/0
	############
	#ADD VM to none vi
	#############
	for vmleft in vm_raw_list:
		if get_or_none(VM,imageID=vmleft['imageID']) == None:
			recordNewVMtoDB(vmleft)
			vi_hold[0]['vmlist'].append(vmleft)
	vi_hold[0]['vi'] = VI.objects.get(id=0)
	isAdmin = isCloudAdmin(request.user)
	cloudAdminGroup = getCloudAdminGroup()
	
	if isAdmin:
		reqVI = VIrequest.objects.filter(waiting=True)
	else:
		reqVI = VIrequest.objects.filter(owner=request.user,waiting=True)
	args = {'vi_id':int(vi_id),'vm_info_list':vm_raw_list,'vi_hold':vi_hold,'currentUser':allActiveUser,'templatelist':templatelist,'isAdmin':isAdmin,'cloudAdminGroup':cloudAdminGroup,'reqVI':reqVI}
	return render_to_response('vi_vm.html',args,context_instance=RequestContext(request))
def vi_tem(request,vi_id):
	return render_to_response('vi_tem.html',{'vi_id':int(vi_id),'allvi':allvi},context_instance=RequestContext(request)) 
def vi_user(request,vi_id):	
	return render_to_response('vi_user.html',{'vi_id':int(vi_id),'allvi':allvi},context_instance=RequestContext(request)) 
def	vi_del(request,vi_id):
	#delete all VM??
	if vi_id != '0' :
		targetVI = VI.objects.get(id=vi_id)
		if targetVI.owner == request.user or isCloudAdmin(request.user):
			vmInList = VM.objects.filter(ownerVI=vi_id)
			for vm in vmInList:
				vm.ownerVI = VI.objects.get(id=0)
			globalVI = getCurrentGlobalVI()
			globalVI.quotaIP = globalVI.quotaIP + targetVI.quotaIP
			globalVI.save()
			targetVI.delete()
	return redirect('/vi')
def createVI_view(request):
	globalVI = getCurrentGlobalVI()
	requestIP = int(request.POST['quotaIP'])
	if isCloudAdmin(request.user):
		if get_or_none(VI,name=request.POST['name']) == None:
			if requestIP <= globalVI.quotaIP - globalVI.usedIP:
				createVI(request.POST['name'],
				request.user,
				request.POST.getlist('isAdmin'),
				request.POST.getlist('isTemplate'),
				int(request.POST['quotaIP']),
				int(request.POST['quotaCPU']),
				int(request.POST['quotaRAM'])
				)
				return HttpResponse("clear")
			else:
				return HttpResponse('error: Insufficient Resource :'+str(globalVI.quotaIP - globalVI.usedIP)+" IP Addresss left")
		else:
			return HttpResponse("Error! : VI request name already exist")
	else:
		if get_or_none(VI,name=request.POST['name']) == None:
			if requestIP <= globalVI.quotaIP - globalVI.usedIP:
				logStatus = logVI(request.POST['name'],
					request.user,
					request.POST.getlist('isAdmin'),
					request.POST.getlist('isTemplate'),
					int(request.POST['quotaIP']),
					int(request.POST['quotaCPU']),
					int(request.POST['quotaRAM'])
					)
				return HttpResponse("clear")
			else:
				return HttpResponse('error: Insufficient Resource :'+str(globalVI.quotaIP - globalVI.usedIP)+" IP Addresss left")
		else:
			return HttpResponse("Error! : VI request name already exist")
def requestVI(request):
	if not isCloudAdmin(request.user):
		return redirect('/')
	gVI = getCurrentGlobalVI()
	req = VIrequest.objects.filter(waiting=True)
	ratioIP = float(gVI.usedIP)/float(gVI.quotaIP)*100
	return render_to_response('req.html',{'ratioIP':ratioIP,'req_list':req,'global_vi':gVI},context_instance=RequestContext(request))
def requestVIConfirm(request):
	if not isCloudAdmin(request.user):
		return redirect('/')
	req_id = request.POST['reqID']
	command = request.POST['command']
	req = VIrequest.objects.get(id=req_id)
	gVI = getCurrentGlobalVI()
	if command == 'accept':
		if get_or_none(VI,name=req.name) == None:
			if req.quotaIP <= gVI.quotaIP - gVI.usedIP:
				adminGroupID = []
				templateListID =[]
				for admin in req.adminGroup.all():
					adminGroupID.append(admin.id)
				for template in req.template.all():
					templateListID.append(template.id)
				createVI(req.name,
				req.owner,
				adminGroupID,
				templateListID,
				req.quotaIP,
				req.quotaVCPU,
				req.quotaRAM)
				req.accept = True
				req.waiting = False
				req.save()
				return HttpResponse("clear")
			else:
				return HttpResponse('error: Insufficient Resource :'+str(gVI.quotaIP - gVI.usedIP)+" IP Addresss left")
		else:
			return HttpResponse("Error! : VI request name already exist")
	elif command == 'decline':
		req.accept = False
		req.waiting = False
		req.save()	
	return redirect('/request')
def editVI(request):
	if request.method == 'POST':
		if not isCloudAdmin(request.user):
			return HttpResponse("Don't have permission")
		gVI = getCurrentGlobalVI()
		viid = int(request.POST['viid'])
		IP = int(request.POST['IP'])
		CPU = int(request.POST['CPU'])
		RAM = int(request.POST['RAM'])
		vi = get_or_none(VI,id=viid)
		if IP > vi.quotaIP:
			if IP - vi.quotaIP > gVI.quotaIP - gVI.usedIP:
				return HttpResponse("Global is out of resource")
			else:
				gVI.quotaIP = gVI.quotaIP - (IP - vi.quotaIP)
				gVI.save()
				vi.quotaIP = IP
				vi.quotaVCPU = CPU
				vi.quotaRAM = RAM
				vi.save()
				return HttpResponse("clear")
		else:
			if IP < vi.usedIP or IP < 1:
				return HttpResponse("Lack to used Resource")
			else:
				gVI.quotaIP = gVI.quotaIP - (IP - vi.quotaIP)
				gVI.save()
				vi.quotaIP = IP
				vi.quotaVCPU = CPU
				vi.quotaRAM = RAM
				vi.save()
				return HttpResponse("clear")
def sendComm(request):
	if request.method == 'POST':
		comm = request.POST['com']
		x = cloud_rURL(comm)
	else:
		comm = request.GET['com']
		x = cloud_rURL(comm)
	# if comm.find('/task/poll/?taskID') != -1:
		# log = setVMLogDetail(x)
		# if log.status == 'finish':
			# if log.action == "destroy":
				# VM.objects.get(imageID=log.vmImageID).delete()
		# if log.status == 'working' and log.action == "create":
			# newip = VM.objects.get(imageID=log.vmImageID).IP
			# pos = x.find('</response>')
			# x = x[:pos] + '<guestIP>'+newip+'</guestIP>'+ x[pos:]
	return HttpResponse(x)	
def pollTask(request):
	taskID = request.POST['taskID']
	x = cloud_rURL("/task/poll/?taskID="+taskID)
	if x != '':
		if isHostTask(x):
			log = setHostLogDetail(x)
		else:
			log = setVMLogDetail(x)
			if log.status == 'finish':
				if log.action == "destroy":
					if get_or_none(VM,imageID=log.vmImageID) != None:
						removeAllocateResouce(VM.objects.get(imageID=log.vmImageID))
						VM.objects.get(imageID=log.vmImageID).delete()
				if log.action == "create":
					if log.error == False:
						newip = VM.objects.get(imageID=log.vmImageID).IP
						pos = x.find('</response>')
						x = x[:pos] + '<guestIP>'+newip+'</guestIP>'+ x[pos:]
	return HttpResponse(x)
def controlVM(request):
	vmid = int(request.POST['vmid'])
	command = request.POST['comm']
	vi = VM.objects.get(imageID=vmid).ownerVI
	if not checkUserPermission(request.user,vi,['vmControl']):
		return HttpResponse(permissionFail(vi,command))
	if command == "destroy" and not checkUserPermission(request.user,vi,['vmDelete']):
		return HttpResponse(permissionFail(vi,command))
	x = cloud_rURL('/guest/'+command+'/?guestID='+str(vmid))
	if x != '':
		createVMLog(vmid,VM.objects.get(imageID=vmid).name,request.user,command,x,vi.id)
	return HttpResponse(x)
# def deleteVMData(request):
	# vi = VM.objects.get(imageID=request.POST['vmid']).ownerVI
	# if checkUserPermission(request.user,vi,['vmDelete']):
		# permissionFail(vi,"delete")
	# vmid = request.POST['vmid']
	# VM.objects.get(imageID=vmid).delete()
	# return HttpResponse("clear")
def controlHost(request):
	hostID = request.POST['hostID']
	com = request.POST['comm']
	if isCloudAdmin(request.user):
		if com == 'close':
			command = 'close?hostID='+hostID+'&mode=shutdown'
			action = 'closehost'
		elif com == 'start':
			command = 'wakeup?hostID='+hostID
			action = 'wakeuphost'
		elif com == 'destroy':
			command = 'remove?hostID='+hostID
			action = 'removehost'
		else:
			return HttpResponse('error')
		x = cloud_rURL('/host/'+command)
		if x != '':
			createHostLog(hostID,request.user,action,x)
		return HttpResponse(x)
	else:
		return HttpResponse("Don't have permission")
def createVM(request):
	vi = VI.objects.get(id=request.POST['new_vm_vi'])
	if not checkUserPermission(request.user,vi,['vmCreate']):
		return HttpResponse(permissionFail(vi,"create"))
	guestName = request.POST['new_vm_name']
	templateID = request.POST['new_vm_template']
	memory = request.POST['new_vm_memory']
	vCPU = request.POST['new_vm_vCPU']
	#inbound = request.POST['new_vm_Inbound']
	#outbound = request.POST['new_vm_Outbound']
	if checkQuotaVI(vi,int(vCPU),int(memory)/256):
		com = "/guest/create?guestName="+guestName+"&templateID="+templateID+"&memory="+memory+"&vCPU="+vCPU
		#if vi.quotaIP <= 1:
		#	return 
		if request.POST.has_key('new_vm_Inbound'):
			inbound = request.POST['new_vm_Inbound']
			if not inbound =='':
				com += "&inbound="+inbound
		if request.POST.has_key('outbound'):
			outbound = request.POST['new_vm_Outbound']
			if not outbound == '':
				com += "&outbound="+outbound
		res = cloud_rURL(com) 
		if res != '': 
			createVMLog(None,request.POST['new_vm_name'],request.user,'create',res,vi.id)
		return HttpResponse(res)
	else:
		return HttpResponse("Out of resources")
def moveVM(request):
	user = request.user
	vmid = int(request.POST['vmid'])
	if get_or_none(VM,imageID=vmid) == None:
		recordNewVMtoDB(getVMinfo(vmid),vmid)
	movedVM = VM.objects.get(imageID=vmid)
	visrc = VI.objects.get(id=request.POST['visrc'])
	#check create permission
	vidst = VI.objects.get(id=request.POST['vidst'])
	if get_or_none(Role,user=user,ownerVI=vidst,vmCreate=True,templateAdd=True) == None:
		return HttpResponse("don't have permission to create VM in "+vidst.name)
	#check delete permission
	#if not request.POST['visrc'] == 0:
	visrc = VI.objects.get(id=request.POST['visrc'])
	if get_or_none(Role,user=user,ownerVI=visrc,vmDelete=True,templateAdd=True) == None:
		return HttpResponse("don't have permission to delete VM in "+visrc.name)
	movedVM.ownerVI = vidst
	movedVM.save()
	return HttpResponse("clear")
	#check anothe create permission
def createRole(request):
	vi = VI.objects.get(id=request.POST['vi_id'])
	rolename = request.POST['new_roleName']
	permission = [False]
	permission.append(request.POST.has_key('new_userAdd'))
	permission.append(request.POST.has_key('new_userRemove'))
	permission.append(request.POST.has_key('new_vmControl'))
	permission.append(request.POST.has_key('new_vmCreate'))
	permission.append(request.POST.has_key('new_vmDelete'))
	permission.append(request.POST.has_key('new_templateAdd'))
	permission.append(request.POST.has_key('new_templateRemove'))
	if not checkUserPermission(request.user,vi,['roleEdit']):
		return permissionFail(vi,command)
	if get_or_none(Role,name=rolename,ownerVI=vi) == None:
		createNewRole(rolename,vi,permission,True)
		return HttpResponse("clear")
	return HttpResponse("This role already exists")
def editRole(request):
	vi = VI.objects.get(id=request.POST['vi_id'])
	role = get_or_none(Role,name=request.POST['roleName'],ownerVI=vi)
	if role == None:
		return HttpResponse("This role doesn't exists")
	permission = [False]
	permission.append(request.POST.has_key('userAdd'))
	permission.append(request.POST.has_key('userRemove'))
	permission.append(request.POST.has_key('vmControl'))
	permission.append(request.POST.has_key('vmCreate'))
	permission.append(request.POST.has_key('vmDelete'))
	permission.append(request.POST.has_key('templateAdd'))
	permission.append(request.POST.has_key('templateRemove'))
	if not checkUserPermission(request.user,vi,['roleEdit']):
		return permissionFail(vi,command)
	configRole(role,permission,True)
	return HttpResponse("clear")
def queryData(request):
	if request.method == 'POST':
		com = request.POST['com']
	else:
		com = request.GET['com']
	user = request.user
	if com == 'getEditUser':
		viid = request.POST['viid']
		userRole = Role.objects.get(ownerVI=VI.objects.get(id=viid),user=user)
		allRole = Role.objects.filter(ownerVI=VI.objects.get(id=viid))
		canAdd = []
		canDelete = []
		for role in allRole:
			if roleGreaterAndEqualDegree(userRole,role):
				canAdd.append(role.id)
				if not roleEqualDegree(userRole,role) or (user==VI.objects.get(id=viid).owner):
					canDelete.append(role.id)
		out = {'viid':viid,'canAdd':canAdd,'canDelete':canDelete}
		return HttpResponse(json.dumps(out))
	elif com == 'getGuestInfo':
		vmlist = request.GET['vmlist']
		getCPU = request.GET['getCPU'] 
		getMEM = request.GET['getMEM'] 
		getNET = request.GET['getNET'] 
		getIO = request.GET['getIO']
		vmlistStat = getVMStat(vmlist,getCPU,getMEM,getNET,getIO)
		return HttpResponse(json.dumps(vmlistStat))
	elif com == 'getHostInfo':
		hostID = request.GET['hostID']
		hostListStat = getHostStat(hostID)
		return HttpResponse(json.dumps(hostListStat))
	elif com == 'getVMDetail':
		vmid = int(request.POST['vmid'])
		vminfo = getVMinfo(vmid)
		templateinfo = getTemplate(vminfo['template'])
		return HttpResponse(json.dumps(dict(vminfo.items()+templateinfo.items())))
	elif com == 'getVILog':
		viid =  request.POST['viid']
		viLog = VMLog.objects.filter(viID=viid)
		logList = [] 
		for log in viLog:
			res = {}
			res['vmName'] = log.vmName
			res['action']= log.action
			res['username']= log.username
			res['finishTime']= log.finishTime
			logList.append(res)
		return HttpResponse(json.dumps(logList))
def moveUser(request):
	userTarget = User.objects.get(id=request.POST['userid'])
	curUser = request.user
	viid = request.POST['viid']
	userRole = Role.objects.get(user = curUser,ownerVI=VI.objects.get(id=viid))
	com = request.POST['com'] 
	if com == 'add':
		roleTarget = Role.objects.get(id=request.POST['roleid'])
		if checkUserPermission(request.user,roleTarget.ownerVI,['userAdd']):
			if roleGreaterAndEqualDegree(userRole,roleTarget):
				roleTarget.user.add(userTarget)
				roleTarget.save()
				return HttpResponse("clear")
		else:
			return HttpResponse("don't have permission "+com)
	elif com == 'remove':
		if isCloudAdmin(userTarget):
			return HttpResponse("Admin cannot be modify")
		old_role = Role.objects.get(id=request.POST['old_roleid'])
		if checkUserPermission(request.user,old_role.ownerVI,['userRemove']):
			if roleGreaterDegree(userRole,old_role) or user==VI.objects.get(id=viid).owner or isCloudAdmin(curUser): 
				old_role.user.remove(userTarget)
				old_role.save()
				return HttpResponse("clear")
			else:
				return HttpResponse("you role doesn't have permission to remove user from "+old_role.name)
		else: 
			return HttpResponse("don't have permission to "+com+" user")
	elif com == 'move':
		if isCloudAdmin(userTarget):
			return HttpResponse("Admin cannot be modify")
		oldRole = Role.objects.get(id=request.POST['old_roleid'])
		roleTarget = Role.objects.get(id=request.POST['roleid'])
		if checkUserPermission(request.user,roleTarget.ownerVI,['userAdd']):
			if roleGreaterDegree or user==VI.objects.get(id=viid).owner or isCloudAdmin(user): 
				roleTarget.user.add(userTarget)
				oldRole.user.remove(userTarget)
				oldRole.save()
				roleTarget.save()
				return HttpResponse("clear")
		else:
			return HttpResponse("don't have permission "+com)
def user(request):
	wrongold = False
	notmatch = False
	changed = False
	if request.method == 'POST':
		wrongold = not request.user.check_password(request.POST['old_password'])
		notmatch = not request.POST['new_password1'] == request.POST['new_password2']
		if not wrongold and not notmatch:
			changed = True
			request.user.set_password(request.POST['new_password1'])
			request.user.save()
	return render_to_response('user.html',{'wrongold':wrongold,'notmatch':notmatch,'changed':changed},context_instance=RequestContext(request))
def host_view(request):
	if not isCloudAdmin(request.user):
		return redirect('/')
	allHost = getHostInfo()
	#allHost = Host.objects.all()
	return render_to_response('host.html',{'allhost':allHost},context_instance=RequestContext(request))
def addHost(request):
	hostName = request.POST['new_host_Name']
	MACAddress = request.POST['new_host_MAC']
	IPAddress = request.POST['new_host_IP']
	com = "/host/add?hostName="+hostName+"&MACAddress="+MACAddress+"&IPAddress="+IPAddress
	res = cloud_rURL(com)
	createHostLog(None,request.user,'host_add',res)
	return HttpResponse(res)
	#if get_or_none(Host,hostName=hostName) == None:
	#	com = "/host/add?hostName="+hostName+"&MACAddress="+MACAddress+"&IPAddress="+IPAddress
	#	res = cloud_rURL(com)
	#	if res != '':
	#		Host.objects.create(MAC=MACAddress,IP=IPAddress,hostName=hostName,owner=getCurrentCloud())
	#	return HttpResponse(res)
	#return render_to_response('host.html',{'allhost':allHost},context_instance=RequestContext(request))
	#return HttpResponse(com)
	#else:
	#	return HttpResponse('Host already added')