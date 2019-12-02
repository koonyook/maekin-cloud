	popupText = []
	taskQueue = []
function isShowCPUinfo(id){
	listPic = ["/media/image/vm_16.png","/media/image/vm_32.png","/media/image/vm_50.png","/media/image/vm_64.png","/media/image/vm_85.png","/media/image/vm_100.png"];
	if(jQuery.inArray($("#vm_avt_"+id+"").attr("src"),listPic) != -1){
		return true;
	}
	return false;
}
function getAllVMidList(){
	x = ""

	$("div.vm_object").each(function(){
		vmid = getID($(this))
		//alert(vmid);
		if($("#vm_runState_"+vmid)[0].innerHTML == 'running')
			x += vmid+',';
		checkActivityOnce(vmid)   
		/////
		/////For check every 5s
		/////
	})
	x = x.substring(0, x.length - 1);
	return x;
}
function changeCurrentCPUInfo(){
	vmidList = getAllVMidList()
	getvmInfo(vmidList,1,0,0,0,decodeVMStat);
}
function decodeVMStat(res,status){
	if(res.responText != ""){
		//popAlert(res.responseText);
		data = jQuery.parseJSON(res.responseText)
		for (var i = 0 ; i < data.length ; i++){
			vmstat =  data[i];
			vmid = vmstat.vmID;
			if($("#vm_runState_"+vmid+"")[0].innerHTML == 'running'){
				if(vmstat.cpuAverage < 16)
					$("#vm_avt_"+vmid+"").attr("src","/media/image/vm_16.png")
				else if(vmstat.cpuAverage < 32)
					$("#vm_avt_"+vmid+"").attr("src","/media/image/vm_32.png")
				else if(vmstat.cpuAverage < 50)
					$("#vm_avt_"+vmid+"").attr("src","/media/image/vm_50.png")
				else if(vmstat.cpuAverage < 64)
					$("#vm_avt_"+vmid+"").attr("src","/media/image/vm_64.png")
				else if(vmstat.cpuAverage < 85)
					$("#vm_avt_"+vmid+"").attr("src","/media/image/vm_85.png")
				else // <100
					$("#vm_avt_"+vmid+"").attr("src","/media/image/vm_100.png")
			}
		}
	}
	setTimeout(changeCurrentCPUInfo,autoPollTime);
}
function getvmInfo(idlist,cpu,mem,net,io,callback){
	var data = {com:"getGuestInfo",vmlist:idlist,getCPU:cpu,getMEM:mem,getNET:net,getIO:io}
	var args = {type:"GET",url:'/queryData',data:data,complete:callback}
	$.ajax(args)
}
function pollGuestInfo(id){
	var data = {com:"/guest/getCustomizedInfo?cpu=1&memory=1&network=1&io=1&guestIDs="+id}
	var args = {type:"GET",url:'/sendComm',data:data,complete:function(res,status){
		if(status=="success"){
		var xmlDoc = $.parseXML( res.responseText )
		var $xml = $( xmlDoc )
		if(($xml).find("response").attr("type") == "error")
		{
			//$("span#vm_curNET_val_"+id+"")[0].innerHTML = "Monitoring Error"
		}
		else{
			var id = $xml.find("guest").attr("guestID");
			var average = $xml.find("average").text()/1;
			var cpuTime = $xml.find("cpuTime").text()/1000000;
			var memTotal = $xml.find("memTotal").text()/1000000;
			var memUse = $xml.find("memUse").text()/1000000;
			var rx = $xml.find("rx").text()/8/1024;
			var tx = $xml.find("tx").text()/8/1024;
			var sumRx = $xml.find("sumRx").text()/8/1024;
			var sumTx = $xml.find("sumTx").text()/8/1024;
			changeGuestInfo(id,average,cpuTime,memTotal,memUse)
			$("span#vm_curNET_val_"+id+"")[0].innerHTML = rx.toFixed(2)+" : "+tx.toFixed(2)+" ["+sumRx.toFixed(2)+":"+sumTx.toFixed(2)+"]";
			$("span#vm_curMEM_val_"+id+"")[0].innerHTML = memUse.toFixed(2)+" : "+memTotal.toFixed(2)+" MB";
			$("span#vm_curCPU_val_"+id+"")[0].innerHTML = average.toFixed(2)+"% : "+cpuTime+"sec";
		}
	}
	else
		popAlert(res.responseText);
	//if(!$("div#vm_"+id+"_info").is(':hidden'))
	if(!$("div#vm_"+id).is(':hidden'))
		setTimeout("pollMonitor("+id+")",delayPollTime)
	}};
	$.ajax(args)
}
function pollMonitor(id){
	if ($("span#"+"_status"+id)[0].innerHTML == "on")
		pollGuestInfo(id)
	else
	{
		$("span#vm_curCPU_val_"+id+"")[0].innerHTML = "Offline"
		$("span#vm_curMEM_val_"+id+"")[0].innerHTML = "Offline"
		$("span#vm_curNET_val_"+id+"")[0].innerHTML = "Offline"
	}
}
function waitForVMID(res,status)
{
	var xmlDoc = $.parseXML( res.responseText );
	var $xml = $( xmlDoc );
	var stat = $xml.find("status").text();
	var taskID = $xml.find("task").attr("taskID");
	var finish = $xml.find("finishStatus").text();
	//alert(res.responseText);
	if (stat == "0" || stat=="1" )
	{
		//alert("poll"+taskID);
		setTimeout(function(){
			pollTask(taskID,waitForVMID);
			//postBack("/pollTask",{taskID:taskID},waitForVMID);
		},delayPollTime)
	}
	else{
		if(finish == '1'){
			newID = $xml.find("guest").attr("guestID");
			if(newID != undefined){
				newIP = $xml.find("guestIP").text();
				vmIns = $("#vm_wait");
				vmIns[0].id = "vm_"+newID;
				vmIns.removeClass("new_vm_object");
				vmIns.addClass("vm_object");
				vmIns.children(".vmmemory")[0]= "vm_memory_"+newID+"";
				vmIns.children(".vmvCPU")[0]= "vm_vCPU_"+newID+"";
				vmIns.children(".vmAvatar")[0].id = "vm_avtdiv_"+newID+"";
				vmIns.children(".vmAvatar").children("img#vm_avt_n")[0].id = "vm_avt_"+newID+""
				vmIns.children("span.vm_name")[0].id =  "vm_name_"+newID+"";
				vmIns.children("span.vm_IP")[0].id =  "vm_IP_"+newID+"";
				vmIns.children("span.vmstatus")[0].id = "vm_status_"+newID+"";
				vmIns.children("span.vmactivity")[0].id =  "vm_act_"+newID+"";
				vmIns.children("span.vmcanControl")[0].id =  "vm_vmcanControl_"+newID+"";
				vmIns.children(".vmAvatar").children(".vm_wait_image")[0].id =  "vm_wait_"+newID+"";
				vmIns.children(".vmAvatar").children(".vm_menu")[0].id =  "vm_menu_"+newID;
				vmIns.children("span.vmrunningState")[0].id =  "vm_runState_"+newID+"";
				//postBack("moveVM",{vmid:newID,visrc:0,vidst:vmIns.parent()[0].id.split('_')[2]})
				$("#vm_IP_"+newID+"").text(newIP);
				$("#vm_"+newID+" .vmAvatar").append('<progress id="vm_progress_'+newID+'"value="0" max="100" ></progress>')
				$("#vm_avtdiv_"+newID).hover(overlayVM,removeOverlayVM);
				pollTask(taskID,repeatPollTask);
				checkDisableCreateVMBttn(getVIOwner(newID,"id"));
			}
			else{
				popAlert($xml.find("finishMessage").text());
			}
		}
		else{
			$("#vm_wait").remove();
		}
	}
}
function createVM(){
	var data = $(this).serializeArray();
	if(checkDisableCreateVMBttn(data[1].value)){
		/*0 = csrftoken,1 = vi,2 = name,3 = template,4 = memory,5 = cpu,6 = inbound,7 = outbound*/
		vmIns = $("#vm_n").clone()
		postBack("/createVM",$.param(data),function(res,status){
			if(status=="success"){
				if(res.responseText == "Out of resources"){
					errorSetup(res.responseText);
				}
				else if (res.responseText.indexOf("Don't have permission") < 0){
					//alert(res.responseText);
					var xmlDoc = $.parseXML( res.responseText );
					var $xml = $( xmlDoc );
					var taskID = $xml.find("task").attr("taskID");
					vmIns[0].id = "vm_wait";
					$(vmIns).children("span.vm_name")[0].innerHTML = data[2].value;
					$(vmIns).children("span.vmvCPU")[0].innerHTML = data[5].value;
					$(vmIns).children("span.vmmemory")[0].innerHTML = data[4].value;
					//$(vmIns).children("span.vm_movearea").children(".vm_name")[0].innerHTML = data[2].value;
					setUsedQouta(data[1].value,1,parseInt(data[5].value),parseInt(data[4].value/256))
					$("#vm_vi_"+data[1].value).append($(vmIns));
					vmIns.show();
					pollTask(taskID,waitForVMID)
					//postBack("/pollTask",{taskID:taskID},waitForVMID);
				}
				else{
					errorSetup(res.responseText);
				}
			}
			else {
				popAlert(res.responseText);
			}
		});
		//$("form.createVMForm").hide();
		removeWrap();
	}
	else{
		removeWrap();
		viname = $("#vi_tag_"+data[1].value).text()
		errorSetup(viname+" is out of resources");
	}
	return false;
}
function chooseTemplate(){
	min = parseInt($("#mem_template_"+$(this).val()).text().split(',')[0])
	max = parseInt($("#mem_template_"+$(this).val()).text().split(',')[1])
	$(".newvm_memory").each(function(){ 
		if (parseInt($(this).val()) < min || parseInt($(this).val()) > max)
			$(this).attr("disabled", "disabled"); 
		else
			$(this).removeAttr("disabled");
		})
	$($(".newvm_memory").not("[disabled=disabled]")[0]).attr('checked', true)
	checkCreateVMInput()
}
function checkCreateVMInput(){
	check = true;
	if($("#new_vm_template_select").val() != "0" &&  $(".input_name").val()!= "" && isCharAndNumber($(".input_name").val()))
		$("#CreateVM").removeAttr('disabled');
}
function checkChangeVI(vmid,visrc,vidst){
	if(visrc == vidst)
		return; //sort?
	postBack("/moveVM",{vmid:vmid,visrc:visrc,vidst:vidst},function(data){
		//alert(data.responseText);
		if(data.responseText != "clear")
			popAlert(data.responseText);
		else{
			$("#vm_vi_"+vidst).append($("#vm_"+vmid))
		}
	})
}
function setMoveVM(){
	// need to polish
	$(".vm_object").draggable({containment: ".vm_vi_list",revert:"invalid",helper:"clone",handle:".vm_name"})
	$(".vi_tag").droppable({hoverClass:"vi_targeted",greedy: true,accept:".vm_object",drop:function(event,ui){
		checkChangeVI(ui.draggable.attr("id").split("_")[1],ui.draggable.parent()[0].id.split("_")[2],$(this).attr("id").split("_")[2])
		}});
	
}
function toggleSelectVM(){
	$(".vm_object").click(function(){
		if(!$(this).hasClass("vm_selected")){
			$(this).addClass("vm_selected");
		}
		else{
			$(this).removeClass("vm_selected");
		}
	})
	/*$("a.show_detail").click(function(){
	if($("div#vm_"+$(this).attr("value")+"_info").is(':hidden'))
		pollMonitor($(this).attr("value"))
	$("div#vm_"+$(this).attr("value")+"_info").slideToggle('fast')
	return false})*/
}
function getVIOwner(vmid,value){
	if(value == "name")
		return $("#vi_tag_"+($("#vm_"+vmid).parent().attr('id').split('_')[2])).text();
	else if(value == "id")
		return $("#vm_"+vmid).parent().attr('id').split('_')[2];
}
function checkPermission(viid,command){
	return ($("#vi_role_"+command+"_"+viid).text().trim() == "True");
} 
function overlayVM(){
	$(this).addClass("vm_showMenu");
	vmid = getID($(this));
	//|| checkPermission(getVIOwner(vmid,'id'),"vmControl")
	if($("#vm_vmcanControl_"+vmid+"").text() == "free" ){ 
		$("#vm_wait_"+vmid+"").hide();
		runState = $("#vm_runState_"+vmid+"").text()
		status = $("#vm_status_"+vmid+"").text()
		act = $("#vm_act_"+vmid+"").text()
		item_menu = ''
		if(runState == "running"){
			item_menu += '<img src="/media/image/bttn_pause.png"  value="suspend" class="bttn_vm_overlay bttn_center">';
			item_menu += '<img src="/media/image/bttn_off.png"  value="forceOff" class="bttn_vm_overlay bttn_left">';
			item_menu += '<img src="/media/image/bttn_advance.png" value="advance" class="bttn_vm_overlay bttn_right">';
		}
		else if(runState == "paused"){
			item_menu += '<img src="/media/image/bttn_play.png"  value="resume" class="bttn_vm_overlay bttn_center" >';
			item_menu += '<img src="/media/image/bttn_off.png"  value="forceOff" class="bttn_vm_overlay bttn_left">';
			item_menu += '<img src="/media/image/bttn_advance.png"  value="advance" class="bttn_vm_overlay bttn_right">';
		}
		else if(status == "saved"){
			item_menu += '<img src="/media/image/bttn_play.png" value="start"  class="bttn_vm_overlay bttn_center">';
			item_menu += '<img src="/media/image/bttn_advance.png" value="advance" class="bttn_vm_overlay bttn_center">';
		}
		else{ //shutoff
			item_menu += '<img src="/media/image/bttn_play.png" value="start"  class="bttn_vm_overlay bttn_center">';
			item_menu += '<img src="/media/image/bttn_advance.png" value="advance" class="bttn_vm_overlay bttn_center">';
		}
		$(this).children(".vm_menu")[0].innerHTML = item_menu;
		$(this).children(".vm_menu").show();
		$(".vm_menu img").hover(hoverBttn,disHoverBttn);
		$(".vm_menu img").click(overlayControl);
	}
	else{
		item_menu = '<img src="/media/image/bttn_advance.png" value="advance" class="bttn_vm_overlay">'
		$(this).children(".vm_menu")[0].innerHTML = item_menu;
		$(this).children(".vm_menu").show();
		$(".vm_menu img").hover(hoverBttn,disHoverBttn);
		$(".vm_menu img").click(overlayControl);
	}
}
function removeOverlayVM(){
	$(this).removeClass("vm_showMenu");
	$(this).children(".vm_menu").hide();
}
function hoverBttn(){
$(this).addClass('bttn_vm_overlay_ch');	//$(this).attr("src",$(this).attr("src").split('.')[0]+'_ch.png');
}
function disHoverBttn(){
$(this).removeClass('bttn_vm_overlay_ch');	
	//imgPath = $(this).attr("src").split('_');
	//$(this).attr("src",imgPath[0]+'_'+imgPath[1]+'.png')
}
function overlayControl(){
	vmid = $($(this)[0]).parent().attr('id').split('_')[2];
	command = $(this).attr('value');
	removeWrap();
	$("#vm_menu_"+vmid).hide();
	if( command == "destroy"){
		text = "Delete VM "+$("#vm_name_"+vmid+"").text()
		alertSetup(text,
			function(){
				removeWrap();
				$("#vm_vmcanControl_"+vmid+"").text("command"); 
				toggleVMWait(vmid);
				postBack("/controlVM",{comm:command,vmid:vmid},checkForPollTask);	
			},
			function(){
				removeWrap();
			})
	}
	else if( command != "advance"){
		$("#vm_vmcanControl_"+vmid+"").text("command"); 
		toggleVMWait(vmid);
		postBack("/controlVM",{comm:command,vmid:vmid},checkForPollTask);
	}
	else{
		getVMDetail(vmid);
	}
}
function toggleVMWait(vmid){
	//alert($("#vm_vmcanControl_"+vmid+"").text() );
	if($("#vm_vmcanControl_"+vmid+"").text() == 'command'){
		$("#vm_wait_"+vmid+"").show();
	}
	else
		$("#vm_wait_"+vmid+"").hide();
}
function getVMDetail(vmid){
	$(".vm_advance_name").text($("#vm_name_"+vmid+"").text() );
	$(".vm_advance_ip").text($("#vm_IP_"+vmid+"").text() );
	$(".vm_advance_vi").text(getVIOwner(vmid,'name'));
	$(".vm_advance_host").text('');
	$(".vm_advance_ip2").text($("#vm_IP_"+vmid+"").text());
	$(".vm_advance_MAC").text('');
	$(".vm_advance_CPU").text($("#vm_vCPU_"+vmid+"").text());
	$(".vm_advance_RAM").text($("#vm_memory_"+vmid+"").text());
	$(".vm_advance_templateID").text('');
	$(".vm_advance_inbound").text('');
	$(".vm_advance_outbound").text('');
	$(".vm_advance_menu")[0].id =  "vm_admenu_"+vmid;
	$(".vm_advance_menu_more")[0].id = "vm_admenumore_"+vmid;
	$(".vm_advance_OS").text('');
	$(".vm_advance_templateDesc").text('');
	$(".vm_advance_templateMin").text('');
	$(".vm_advance_templateMax").text('');
	$(".vm_advance_info_waiting").show();
	$(".bttn_vm_advance").unbind();
	if($("#vm_vmcanControl_"+vmid+"").text() != "free" ||  $("#vm_act_"+vmid+"").text() != "none" ){
		$("#bttn_vm_advance_play").addClass('bttn_vm_advance_disable');
		$("#bttn_vm_advance_off").addClass('bttn_vm_advance_disable');
		$("#bttn_vm_advance_save").addClass('bttn_vm_advance_disable');
		$("#bttn_vm_advance_pause").addClass('bttn_vm_advance_disable');
		$("#bttn_vm_advance_delete").addClass('bttn_vm_advance_disable');
	}
	else{
		if($("#vm_runState_"+vmid+"").text() == "running"){
				$("#bttn_vm_advance_play").addClass('bttn_vm_advance_disable');
				$(".bttn_down_vm").removeClass('bttn_vm_advance_disable');
		}
		else{
			$("#bttn_vm_advance_play").removeClass('bttn_vm_advance_disable');
			if($("#vm_runState_"+vmid+"").text()== "paused"){
				$("#bttn_vm_advance_play").attr('value',"resume");
				$("#bttn_vm_advance_pause").addClass('bttn_vm_advance_disable');
			}
			else{	//shutoff
				$("#bttn_vm_advance_play").attr('value',"start");
				$("#bttn_vm_advance_off").addClass('bttn_vm_advance_disable');
				$("#bttn_vm_advance_pause").addClass('bttn_vm_advance_disable');
				$("#bttn_vm_advance_save").addClass('bttn_vm_advance_disable');
			}
		} 
	}
	$(".bttn_vm_advance").not(".bttn_vm_advance_disable").hover(hoverBttn,disHoverBttn);
	$(".bttn_vm_advance").not(".bttn_vm_advance_disable").unbind("click")
	$(".bttn_vm_advance").not(".bttn_vm_advance_disable").click(overlayControl);
	addWrap($(".vm_advance_form"),2);
	//SYNC Online Data
	postBack('/queryData',{com:'getVMDetail',vmid:vmid},function(res,status){
		data = jQuery.parseJSON(res.responseText);
		$(".vm_advance_name").text(data.name);
		$(".vm_advance_ip").text(data.IP);
		$(".vm_advance_vi").text($("#vi_tag_"+data.ownerVI).text());
		/* $(".vm_advacnce_activity").text(data.activity);
		$(".vm_advacnce_state").text(data.runningState);
		$(".vm_advacnce_status").text(data.status); */
		$(".vm_advance_host").text(data.hostid);
		$(".vm_advance_ip2").text(data.IP);
		$(".vm_advance_MAC").text(data.MAC);
		$(".vm_advance_CPU").text(data.vCPU);
		$(".vm_advance_RAM").text(data.memory+" MB");
		$(".vm_advance_templateID").text(data.templateID);
		$(".vm_advance_inbound").text(data.inbound);
		$(".vm_advance_outbound").text(data.outbound);
		$(".vm_advance_menu")[0].id = "vm_admenu_"+data.imageID;
		$(".vm_advance_menu_more")[0].id = "vm_admenumore_"+data.imageID;
		$(".vm_advance_OS").text(data.OS);
		$(".vm_advance_templateDesc").text(data.description);
		$(".vm_advance_templateMin").text(data.minimumMemory);
		$(".vm_advance_templateMax").text(data.maximumMemory);
		$(".bttn_vm_advance").unbind();
		if($("#vm_vmcanControl_"+vmid+"").text() != "free" ||  $("#vm_act_"+vmid+"").text() != "none"){
			$("#bttn_vm_advance_play").addClass('bttn_vm_advance_disable');
			$("#bttn_vm_advance_off").addClass('bttn_vm_advance_disable');
			$("#bttn_vm_advance_save").addClass('bttn_vm_advance_disable');
			$("#bttn_vm_advance_pause").addClass('bttn_vm_advance_disable');
			$("#bttn_vm_advance_delete").addClass('bttn_vm_advance_disable');
			pollStatGraph(vmid,true,false,"vm_graph_cpu","vm_graph_mem","vm_graph_net","vm_graph_io");
		}
		else{
			if($("#vm_runState_"+vmid+"").text() == "running"){
				$("#bttn_vm_advance_play").addClass('bttn_vm_advance_disable');
				$(".bttn_down_vm").removeClass('bttn_vm_advance_disable');
				pollStatGraph(vmid,true,true,"vm_graph_cpu","vm_graph_mem","vm_graph_net","vm_graph_io");
			}
			else{
				$("#bttn_vm_advance_play").removeClass('bttn_vm_advance_disable');
				if($("#vm_runState_"+vmid+"").text()== "paused"){
					$("#bttn_vm_advance_play").attr('value',"resume");
					$("#bttn_vm_advance_pause").addClass('bttn_vm_advance_disable');
				}
				else{	//shutoff
					$("#bttn_vm_advance_play").attr('value',"start");
					$("#bttn_vm_advance_off").addClass('bttn_vm_advance_disable');
					$("#bttn_vm_advance_pause").addClass('bttn_vm_advance_disable');
					$("#bttn_vm_advance_save").addClass('bttn_vm_advance_disable');
				}
				pollStatGraph(vmid,true,false,"vm_graph_cpu","vm_graph_mem","vm_graph_net","vm_graph_io");
			}
		}
		$(".bttn_vm_advance").not(".bttn_vm_advance_disable").hover(hoverBttn,disHoverBttn);
		$(".bttn_vm_advance").not(".bttn_vm_advance_disable").unbind("click")
		$(".bttn_vm_advance").not(".bttn_vm_advance_disable").click(overlayControl);
		$(".vm_advance_info_waiting").hide();
	});
}
function setCurrentVIMenu(){
	var pathname = window.location.pathname;
	urlsplit = pathname.split("/");
	viFocus = 0;
	if(urlsplit.length > 2)
	{
		viFocus = urlsplit[2];
		if(urlsplit[3]=="user")
			toggleVIMenu(viFocus,'vi_menu_user_bttn')
		else if(urlsplit[3]=="template")
			toggleVIMenu(viFocus,'vi_menu_template_bttn')
		else if(urlsplit[3]=="summary")
			toggleVIMenu(viFocus,'vi_menu_summary_bttn')
		else
			toggleVIMenu(viFocus,'vi_menu_vm_bttn')
	}
	else
		toggleVIMenu(viFocus,'vi_menu_vm_bttn')
	$("#vi_tag_"+viFocus).addClass("vi_selected");
	$("#vi_"+viFocus).show();
	if(checkPermission(viFocus,"vmCreate")){
		$("#top_menu_bttn_createVM").show();
	}
	else{
		$("#top_menu_bttn_createVM").hide();
	}
	checkDisableCreateVMBttn(viFocus);
}
function checkQuotaVIResource(viid,cpu,mem){
	usedIP = parseInt($("#vi_used_IP_"+viid).text());
	quotaIP = parseInt($("#vi_quota_IP_"+viid).text());
	usedCPU = parseInt( $("#vi_used_CPU_"+viid).text());
	quotaCPU =parseInt( $("#vi_quota_CPU_"+viid).text());
	usedRAM =  parseInt($("#vi_used_RAM_"+viid).text());
	quotaRAM =parseInt( $("#vi_quota_RAM_"+viid).text());
	if(viid !=0){
	}
	else{
		if (quotaIP - usedIP > 0)
			return true;
		else
			return false;
	}
}
function checkDisableCreateVMBttn(viid){
	usedIP = parseInt($("#vi_used_IP_"+viid).text());
	quotaIP = parseInt($("#vi_quota_IP_"+viid).text());
	usedCPU = parseInt( $("#vi_used_CPU_"+viid).text());
	quotaCPU =parseInt( $("#vi_quota_CPU_"+viid).text());
	usedRAM =  parseInt($("#vi_used_RAM_"+viid).text());
	quotaRAM =parseInt( $("#vi_quota_RAM_"+viid).text());
	check = true;
	if (viid != 0){
		if(usedIP >= quotaIP || usedCPU >= quotaCPU ||usedRAM >= quotaRAM){
			$("#top_menu_bttn_createVM").attr("disabled","disabled");
			$("#top_menu_bttn_createVM").addClass("disabled");
			check = false;
		}
		else{
			$("#top_menu_bttn_createVM").removeAttr("disabled");
			$("#top_menu_bttn_createVM").removeClass("disabled");
		}
	}
	else{
		if(usedIP >= quotaIP){
			$("#top_menu_bttn_createVM").attr("disabled","disabled");
			$("#top_menu_bttn_createVM").addClass("disabled");
			check = false;
		}
		else{
			$("#top_menu_bttn_createVM").removeAttr("disabled");
			$("#top_menu_bttn_createVM").removeClass("disabled");
		}
	}
	return check;
}
function setUsedQouta(viid,ipdif,cpudif,ramdif){
	$("#vi_used_IP_"+viid).text(
		parseInt($("#vi_used_IP_"+viid).text()) +ipdif
		);
	$("#vi_used_CPU_"+viid).text(
		parseInt($("#vi_used_CPU_"+viid).text()) + cpudif
		);
	$("#vi_used_RAM_"+viid).text(
		parseInt($("#vi_used_RAM_"+viid).text()) +ramdif
		);
	perIP = parseFloat($("#vi_used_IP_"+viid).text())/parseFloat($("#vi_quota_IP_"+viid).text())*100;
	perCPU = parseFloat($("#vi_used_CPU_"+viid).text())/parseFloat($("#vi_quota_CPU_"+viid).text())*100;
	perMEM = parseFloat($("#vi_used_RAM_"+viid).text())/parseFloat($("#vi_quota_RAM_"+viid).text())*100;
	$("#bar_IP_"+viid).attr("style","width:"+perIP+"%");
	$("#bar_cpu_"+viid).attr("style","width:"+perCPU+"%");
	$("#bar_mem_"+viid).attr("style","width:"+perMEM+"%");
}
function checkOnlyCharNumber(){
	//alert("test");
	var inp = $(this).val();
	var checkNumberorChar = isCharAndNumber(inp);
	//alert(checkNumberorChar);
	if($(".input_name").val() == ''){
		$("#CreateVM").attr('disabled','disabled');
	}
	else{
		if(!(checkNumberorChar) ){
			$(this).addClass("input_name_error");
			$(this).parent().parent().children(".submitBttnContainer").children(".submitBttnWrapForm").attr("disabled", "disabled");
		}
		else{
			$(this).removeClass("input_name_error");
			checkCreateVMInput();
			//$(this).parent().parent().children(".submitBttnContainer").children(".submitBttnWrapForm").removeAttr("disabled");
		}
	}
}
function setTemplateForCreateVM(viid){
	$("#new_vm_template_select").children().hide();
	$("#vi_template_form_"+viid).children(".template_info").each(function(){
		templateid = getID($(this))
		$("#new_vm_template_select").children("[value="+templateid+"]").show();
	})
	$("input[name=new_vm_name]").val("");
	$("#new_vm_template_select").val(0);
	$(".newvm_memory").removeAttr('disabled');
	$($(".newvm_memory")[0]).attr('checked',true);
	$("#CreateVM").attr('disabled','disabled');
}
function callCreateFromTemplate(){
	var templateid = parseInt(getID($(this)))
	alert(templateid);
	$("#top_menu_bttn_createVM").trigger('click');
	$("#new_vm_template_select").val(templateid);
	$("#new_vm_template_select").trigger('change');
	
}
function refreshLog(viid){
	postBack("/queryData",{com:'getVILog',viid:viid},function(res,status){
		if(status == "success"){
			$("#vi_log_refresh_bttn_"+viid).text("Refresh Log")
			data = jQuery.parseJSON(res.responseText)
			$("#vi_log_form_"+viid).empty();
			var i = 0;
			for(i = data.length - 1 ; i >= 0 ;i--){
				tmp = "";
				tmp = tmp + '<div class="vi_log_detail">'
				tmp = tmp +  '<span class="vi_log_finish">'+data[i].finishTime+'</span>';
				tmp = tmp + '<span class="vi_log_vm">'+data[i].vmName+'</span>';
				tmp = tmp +  '<span class="vi_log_action">'+data[i].action+'</span>';
				tmp = tmp +  '<span class="vi_log_user">'+data[i].username+'</span>';
				//<span class="vi_log_start">{{log.startTime}}</span>
				
				tmp = tmp + '</div>'
				$("#vi_log_form_"+viid)[0].innerHTML = $("#vi_log_form_"+viid)[0].innerHTML+tmp;
				//alert(tmp);
			}
		}
	})
}
function initfunction(){
	$(".template_info_avatar").click(callCreateFromTemplate)
	$(".input_name").keyup(checkOnlyCharNumber);
	$("div.vm_detail").hide();
	//$("form.createVMForm").hide();
	//////////////////////////////;////////
	//VI Delete show alert
	///////////////////////////////////////
	$(".vi_del_bttn").click(function(){
		viid = $(this).parent().attr('id').split('_')[2]
		text = "Delete VI "+$("#vi_tag_"+viid).text()
		alertSetup(text,
			function(){
				window.location.replace("/vi/"+viid+"/deleteVI")
				removeWrap();
			},
			function(){
				removeWrap();
			});
		return false;
	})
	//////////////////////////////;////////
	//Edit VI Quota
	///////////////////////////////////////
	$(".vi_quota_reduce").click(function(){
		viid = getID($(this));
		type = $(this).attr('value');
		oldVal = parseInt($("#vi_quota_"+type+"_"+viid).attr("value"));
		usedVal = parseInt($("#vi_used_"+type+"_"+viid).attr("value"));
		if(oldVal > 1){
			if (usedVal < oldVal ){
				$("#vi_quota_"+type+"_"+viid).attr("value",oldVal-1)
				$("#vi_quota_"+type+"_"+viid).text(oldVal-1)
			}
			else{
				errorSetup("lack to used Resource")
			}
		}
		else
			errorSetup("At Least 1 of resource left")
	});
	$(".vi_quota_add").click(function(){
		viid = getID($(this));
		type = $(this).attr('value');
		oldVal = parseInt($("#vi_quota_"+type+"_"+viid).attr("value"));
		globalLeftVal = parseInt($("#vi_quota_"+type+"_0").attr("value")) - parseInt($("#vi_used_"+type+"_0").attr("value"));
		dif = parseInt($(this).attr('dif'));
		if (globalLeftVal >= dif +1 || type != "IP"){
			$(this).attr('dif', parseInt($(this).attr('dif')) + 1)
			$("#vi_quota_"+type+"_"+viid).attr("value",oldVal+1)
			$("#vi_quota_"+type+"_"+viid).text(oldVal+1)
		}
		else{
			errorSetup("Global is out of resource")
		}
	});
	$(".vi_quota_update").click(function(){
		viid = getID($(this));
		IP = $("#vi_quota_IP_"+viid).attr("value")
		CPU = $("#vi_quota_CPU_"+viid).attr("value")
		RAM = $("#vi_quota_RAM_"+viid).attr("value")
		postBack("/editVIQuota",{'viid':viid,'IP':IP,'CPU':CPU,'RAM':RAM},function(res,status){
			if(status == "success"){
				if(res.responseText == "clear")
				{
					window.location.reload();
				}
			}
			else
				popAlert(res.responseText);
		})
	})
	//////////////////////////////;////////
	//Refresh VI Log
	///////////////////////////////////////
	$(".vi_log_refresh_bttn").click(function(){
		$(this).text("Refreshing")
		refreshLog(getID($(this)))
	});
	//////////////////////////////;////////
	//Show Current VI
	///////////////////////////////////////
	$("div.vi_object").hide();
	$("div#createVI").hide();
	setCurrentVIMenu();
	//////////////////////////////;////////
	//Change VM Create menu from VI
	///////////////////////////////////////
	
	$("#selectvi_newVM").change(function(){
		setTemplateForCreateVM($("#selectvi_newVM").val());
		setCurrentVIMenu();
	});
	$("#top_menu_bttn_createVM").click(function(){
		viid = $(".vi_selected").val();
		$("#selectvi_newVM").val(viid);
		setTemplateForCreateVM(viid);
		$($(".newvm_cpu")[0]).attr('checked',true)
		addWrap($("#createVMForm"),0);
	})
	$("#new_vm_template_select").change(chooseTemplate)
	$("#createVMForm").submit(createVM);
	$("div.vmactivity").hide();
	//$(".vm_vi_list").hide();
	$("div.vmactivity").each(function(){
		if ($("span#"+(this.id).split('_')[2]).innerHTML == "none")
		$(this).hide()
	})
	$(".vmAvatar").hover(overlayVM,removeOverlayVM);
	//checkAllActivity();
	//toggleSelectVM();
	//setMoveVM();
	changeCurrentCPUInfo();
	////////////////////////////////////////
	//// VI MENU
	/////////////////////////////////////////
		//////////////////////////////////////
		// Hide and Show VM from selected VI
		///////////////////////////////////////
		$(".vi_tag").click(function(){
			viid = $(this).attr("value")
			$("div.vi_object").hide();
			$("#vi_"+viid).show();
			$(".vi_tag").removeClass('vi_selected');
			$(this).addClass('vi_selected');
			changeURL($(this).attr('href'));
			setCurrentVIMenu();
			return false;
		});
		$(".vi_tag").hover(function(){$(this).addClass("vi_tag_hover");},function(){$(this).removeClass("vi_tag_hover");})
		//////////////////////////////////////
		//Hide Show VI menu
		///////////////////////////////////////
		$(".vi_menu_tab a").click(function(){
			toggleVIMenu(getID($(this)),$(this).attr('class'))
			//change current url but not load
			changeURL($(this).attr('href'))
			return false;
		})
		//////////////////////////////////////
		//Hide and Show VM list
		///////////////////////////////////////
		/*function initPage(){
			$("div.vi_list").hide();
			$("div#createVI").hide();
			//////////////////////////////;////////
			//Show Current VI
			///////////////////////////////////////
			var pathname = window.location.pathname;
			urlsplit = pathname.split("/");
			viFocus = 0;
			if(urlsplit.length > 2)
			{
				viFocus = urlsplit[2];
				if(urlsplit[3]=="userVICon")
					$("#vi_user_form").show();
				else if(urlsplit[3]=="temVICon")
					$("#vi_template_form").show();
			}
			$("#vi_tag_"+viFocus).addClass("vi_selected");
			$("#vi_"+viFocus).show();
			$("#vi_role_data_"+viFocus).show();
		}*/	
		//////////////////////////////////////
		//Hide and Show Create Form
		///////////////////////////////////////
		//var isCreateHide = true;
		$("input#showCreateVI").click(function(){
				addWrap($("#vi_create_form"),5);
			});
		$("input.checkIsAdmin").click(function(){
			if ($(this).attr("checked") == "checked"){
				$("input#isUser_"+$(this).attr("value")).attr("checked",false);
				$("div#isUser_"+$(this).attr("value")).hide();
			}
			else{
				$("div#isUser_"+$(this).attr("value")).show();
			}
		})
		//////////////////////////////////////
		//Check VI value
		///////////////////////////////////////
		$("#vi_create_form").submit(function(){
			var data = $(this).serializeArray();
			var check = true;
			if ($("#create_vi_new_vi_name").val() == ""){
				$("#create_vi_new_vi_name_error").text("need VI name");
			}
			if (!$("input[name=isTemplate]").is(':checked')){
				$("#create_vi_new_vi_template_error").text("need Template");
			}
			checkQoutaNewVI()
			check = checkVICanCreate();
			if (check){
				postBack("/createVI",$.param(data),function(res,status){
					if(res.responseText != "clear"){
						removeWrap();
						errorSetup(res.responseText);
					}
					else{
						window.location.reload();
					}
				});
			}
			else{
				$("#createVI").attr('disabled','disabled');
				return false;
			}
			return false;
		})
		function checkQoutaNewVI(){
			qIP = $("#quotaIP").trigger("keyup")
			qCPU = $("#quotaCPU").trigger("keyup")
			qRAM = $("#quotaRAM").trigger("keyup")
		}
		function checkVICanCreate(){
		
			if($("#create_vi_new_vi_name_error").text() == "" && 
				$("#create_vi_new_vi_template_error").text()== "" && 
				$("#create_vi_new_vi_qouta_error").text()== "" &&
				$("#quotaIP").val() != ""){
				$("#createVI").removeAttr('disabled')
				return true;
			}
			else
				return false;
		}
		//////////////////////////////////////
		//Change VI value 
		///////////////////////////////////////
		$("#create_vi_new_vi_name").keyup(function(){
			if ($("#create_vi_new_vi_name").val() == ""){
				$("#create_vi_new_vi_name_error").text("need VI name")
			}
			else{
				$("#create_vi_new_vi_name_error").text("");
				checkVICanCreate();
			}
		})
		$("input[name=isTemplate]").change(function(){
			if (!$("input[name=isTemplate]").is(':checked')){
				$("#create_vi_new_vi_template_error").text("need Template")
				$("#createVI").attr('disabled','disabled');
			}
			else{
				$("#create_vi_new_vi_template_error").text("");
				checkVICanCreate();
			}
		})
		$("#quotaIP").keyup(function(){
			if(isNumber($(this).val()) && $("#quotaIP").val().length > 0){
				vmReq = parseInt($(this).val());
				if(vmReq > 0){
					$(this).removeClass('input_name_error');
					$("#quotaCPU").val(vmReq);
					$("#quotaCPU").removeClass('input_name_error')
					$("#quotaRAM").val(vmReq);
					$("#quotaRAM").removeClass('input_name_error')
					$("#create_vi_new_vi_qouta_error").text("");
					checkVICanCreate();
				}
				else{
					$(this).addClass('input_name_error');
					$("#createVI").attr('disabled','disabled');
				}
			}
			else{
				$(this).addClass('input_name_error');
				$("#createVI").attr('disabled','disabled');
			}
		})
		$("#quotaRAM").keyup(function(){
			if(isNumber($(this).val())){
				ramReq = parseInt($(this).val()); 
				if (ramReq >= parseInt($("#quotaIP").val()) && ramReq > 0){
					$(this).removeClass('input_name_error');
					$("#create_vi_new_vi_qouta_error").text("");
					checkVICanCreate();
				}
				else{
					$(this).addClass('input_name_error');
					$("#createVI").attr('disabled','disabled');
				}
			}
			else{
				$(this).addClass('input_name_error');
				$("#createVI").attr('disabled','disabled');
			}
		})
		$("#quotaCPU").keyup(function(){
			if(isNumber($(this).val())){
				cpuReq = parseInt($(this).val())
				if (cpuReq >= parseInt($("#quotaIP").val()) && cpuReq > 0){
					$(this).removeClass('input_name_error');
					$("#create_vi_new_vi_qouta_error").text("");
					checkVICanCreate();
				}
				else{
					$(this).addClass('input_name_error');
					$("#createVI").attr('disabled','disabled');
				}
			}
			else{
				$(this).addClass('input_name_error');
				$("#createVI").attr('disabled','disabled');
			}
		})
		//////////////////////////////////////
		//Toggle User when create VI
		///////////////////////////////////////
		$("input.checkIsUser").click(function(){
			if ($(this).attr("checked") == "checked"){
				$("input#isAdmin_"+$(this).attr("value")).attr("checked",false);
				$("div#isAdmin_"+$(this).attr("value")).hide();
			}
			else{
				$("div#isAdmin_"+$(this).attr("value")).show();
			}
		})
		//////////////////////////////;////////
		// Init VI Menu
		//////////////////////////////;////////
		$("#vi_template_form").hide();
		$("#vi_user_form").hide();
		//$(".vi_role_data").hide();
		$(".user_left_pool").hide();
		$(".perm_pool").hide();
		$(".removeUserBttn").hide();
		//////////////////////////////;////////
		//Remove User From Role
		//////////////////////////////;////////
		$(".removeUserBttn").click(removeUserFromRole)
		//////////////////////////////;////////
		//Set User Move/Unmove able
		//////////////////////////////;////////
		$(".editUserBttn").click(function(){
			viid =  $(this).attr("id").split("_")[1];
			$("#vi_role_userleft_"+viid).toggle();
			//showUserPane;
			postBack("/queryData",{viid:viid,com:'getEditUser'},setMoveUser);
			
		});
		//////////////////////////////;////////
		//Show Add User Pane
		//////////////////////////////;////////
		$(".editRoleBttn").click(function(){
			$("#vi_role_perm_"+$(this).attr('id').split('_')[1]).toggle();
		   });
		$(".vi_role_new").hide();
		$(".addRoleBttn").click(function(){
			$("#vi_role_new_"+$(this).attr('id').split('_')[1]).toggle();
		   });
		 $(".perm_pool").submit(function(){
			
			var data = $(this).serializeArray();
			postBack("/editRole",$.param(data),function(res,status){
				if(res.responseText != "clear")
					errorSetup(res.responseText);
				else{
					curvi = $(this).children("input[name='viid']").attr('value')
					window.location.reload();
				}
			});
			return false;
		})
		$(".vi_role_new_form").submit(function(){
			
			var data = $(this).serializeArray();
			postBack("/createRole",$.param(data),function(res,status){
				if(res.responseText != "clear")
					errorSetup(res.responseText);
				else{
					curvi = $(this).children("input[name='viid']").attr('value')
					window.location.reload();
				}
			});
			return false;
		})
}
$(document).ready(initfunction)