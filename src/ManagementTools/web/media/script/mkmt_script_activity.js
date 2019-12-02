function modifyActivity(res,status){
	if(status == "success"){
		var xmlDoc = $.parseXML( res.responseText )
		var $xml = $( xmlDoc )
		var $act = $xml.find("activity")
		var id = $xml.find("guest").attr("guestID")
		var runState = ['none','running','out of memory','paused','shutting down','shutoff','crashed'][$xml.find("runningState").text()]
		var act = ["none","cloning","booting","saving","restoring"][$act.text()];
		var status = ['shutoff','on','saved'][$xml.find("status").text()]
		if(id != undefined){
			//alert("id>>"+id+",act>>"+act+",  runstate>>"+runState+",  status>>"+status);
			if(("div#vm_"+id).length > 0){
				//alert(">>>"+id+"<<");
				$("span#vm_runState_"+id)[0].innerHTML = runState
				$("span#vm_act_"+id)[0].innerHTML = act
				$("span#vm_status_"+id)[0].innerHTML = status
				if (runState == 'running'){
					if(!isShowCPUinfo(id))
						$("#vm_avt_"+id+"").attr("src","/media/image/vm_on.png");
				}
				else if(runState == 'paused'){
					$("#vm_avt_"+id+"").attr("src","/media/image/vm_pause.png");
				}
				else if(act == 'booting'){
					if ($("#vm_avt_"+id+"").attr("src") != "/media/image/vm_boot.gif")
						$("#vm_avt_"+id+"").attr("src","/media/image/vm_boot.gif");
				}
				else if(act == 'restoring'){
					$("#vm_avt_"+id+"").attr("src","/media/image/vm_boot.gif");
				}
				else if(act == 'saving'){
					if ($("#vm_avt_"+id+"").attr("src") != "/media/image/vm_save.gif")
					$("#vm_avt_"+id+"").attr("src","/media/image/vm_save.gif");
				}
				else if(act == 'cloning'){
					if ($("#vm_avt_"+id+"").attr("src") !="/media/image/vm_clone.gif")
						$("#vm_avt_"+id+"").attr("src","/media/image/vm_clone.gif");
				}
				else if(status == 'shutoff'){
					$("#vm_avt_"+id+"").attr("src","/media/image/vm_off.png");
				}
				else if (status == 'saved')
					$("#vm_avt_"+id+"").attr("src","/media/image/vm_saved.gif");
			}
			if(act != "none" && act != ""){
				$("#vm_vmcanControl_"+id+"").text("working")
				//$("div#vm_"+id+"_act").show()
				return id;
			}
			else {
				if($("#vm_vmcanControl_"+id+"").text() != "command"){
					$("#vm_vmcanControl_"+id+"").text("free")
				}
				////
				////IF user is viewing advance
				////
				//if($("#vm_advance").is(":visible") ){	
				//	getVMDetail(id);	
				//}
				//$("div#vm_act_"+id+"").hide()
				return -1;
			}
		}
		return id;
	}
}
function checkActivityOnce(id){
	postBack("/sendComm",{com:"/guest/getState?guestID="+id},modifyActivity);
}
function pollActivity(id){
	postBack("/sendComm",{com:"/guest/getState?guestID="+id},function(res,status){
		if(status == "success"){
			checkVMID = modifyActivity(res,status);
			//alert(checkVMID);
			if(checkVMID != -1){
				setTimeout("pollActivity("+id+")",delayPollTime)
			}
		}
		else
			//popAlert(res.responseText);
		}
	);
}
function checkAllActivity(){
	for(i = 0;i < $("div.vm_object").length;i++)
		{
			vmid = $("div.vm_object")[i].id.split('_')[len($("div.vm_object")[i].id.split('_')-1)];
			if (vmid != "n")
				setTimeout("pollActivity("+vmid+")",delayPollTime);
		}
}