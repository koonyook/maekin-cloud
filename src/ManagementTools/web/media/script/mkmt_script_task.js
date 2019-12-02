var delayPollTime = 2000;
var autoPollTime = 10000;
function pollTask(taskID,finishCall){
	postBack("/pollTask",{taskID:taskID},finishCall);
}
function checkForPollTask(res,status){
	if(status == "success"){
		if (res.responseText.indexOf("Don't have permission") < 0){
			var $xml = $( $.parseXML( res.responseText ) );
			var taskID = $xml.find("task").attr("taskID");
			//alert("Response Back>>\n"+res.responseText)
			if($xml.find("response").attr("type") == "waiting")
			{
				setTimeout("pollTask("+taskID+",repeatPollTask)",delayPollTime);
			}
		}
		else{
			errorSetup(res.responseText);
			$("#vm_vmcanControl_"+vmid+"").text("free");
			toggleVMWait(vmid);
		}
	}
	else
	{
		//popAlert(res.responseText);
	}
}
function hostCheckWaiting(res,status){
	//popAlert(res.responseText);
	if(status == "success"){
		if (res.responseText.indexOf("Don't have permission") < 0){
			var $xml = $( $.parseXML( res.responseText ) );
			var taskID = $xml.find("task").attr("taskID");
			//alert("Response Back>>\n"+res.responseText)
			if($xml.find("response").attr("type") == "waiting")
			{
				//alert("isWating");
				setTimeout("pollTask("+taskID+",hostRepeatPollTask)",delayPollTime);
			}
			else
			{
				checkHostActivityOnce(hostID)	;
			}
		}
		else{
			errorSetup(res.responseText);
		}
	}
	else{
		alert('fucjjk')
	}
}
function hostRepeatPollTask(res,status){
	//alert("resr:>>>>"+res.responseText);
	if(status == "success"){
		//alert(res.responseText);
		var xmlDoc = $.parseXML( res.responseText );
		var $xml = $( xmlDoc );
		var status = $xml.find("status");
		var finishStatus = $xml.find("finishStatus");
		var taskID = $xml.find("task").attr("taskID");
		var taskDetail = jQuery.parseJSON($xml.find("detail").text())
		var hostID = taskDetail.hostID;
		//alert(hostID);
		//alert(res.responseText);
		if(status.text() == "0")	 // inqueue
		{
			if(taskDetail.command == "host_add")
				$("#addingHost_label").toggle();
			checkHostActivityOnce(hostID)	;
			setTimeout("pollTask("+taskID+",hostRepeatPollTask)",delayPollTime)

		}	
		else if(status.text() == "1"){	//working
			if(taskDetail.command == "host_add")
				$("#addingHost_label").toggle();
			checkHostActivityOnce(hostID)	;
			setTimeout("pollTask("+taskID+",hostRepeatPollTask)",delayPollTime)
		}
		else	//Finish
		{
			checkHostActivityOnce(hostID)	;
			if(taskDetail.command == "host_remove" || taskDetail.command == "host_add"){
				window.location.reload();
			}
		}
	}
	else{
		//alert('sadd');
	}
}
function repeatPollTask(res,status){
	if(status == "success"){
		//alert("Task Back>>\n"+res.responseText);
		var xmlDoc = $.parseXML( res.responseText );
		var $xml = $( xmlDoc );
		var status = $xml.find("status");
		var finishStatus = $xml.find("finishStatus");
		var taskID = $xml.find("task").attr("taskID");
		var taskDetail = jQuery.parseJSON($xml.find("detail").text())
						//alert($xml.find("detail").text())
						//<status>{0: inQueue, 1: working, 2:finished}</status>
						//<finishStauts>{0: None, 1:success, 2:error}</finishStatus>
		var vmID;
		if (taskDetail.command == "guest_create")
		{
			progress = $xml.find("progress").text()
			vmID = $xml.find("guest").attr("guestID");
		}
		else
			vmID = taskDetail.guestID;
						//alert("vm>>"+vmID);
		if(status.text() == "0")	 // inqueue
		{
			$("#vm_vmcanControl_"+vmID).text("command") ;
			checkActivityOnce(vmID)	;
			setTimeout("pollTask("+taskID+",repeatPollTask)",delayPollTime)
			//addPopup($("#vm_"+vmID+" .vm_name")[0].innerHTML+" : "+taskDetail.command,taskID);
		}	
		else if(status.text() == "1"){	//working
			$("#vm_vmcanControl_"+vmID).text("working") ;
			if (taskDetail.command == "guest_create"){
				prog = $xml.find("progress").text();
				$("#vm_progress_"+vmID).attr('value',prog.substring(0, prog.length - 1))
			}
			else if(taskDetail.command == "guest_start"){
				if ($("#vm_avt_"+vmID).attr("src") != "/media/image/vm_boot.gif")
					$("#vm_avt_"+vmID).attr("src","/media/image/vm_boot.gif");
			}
			setTimeout("pollTask("+taskID+",repeatPollTask)",delayPollTime)
			//addPopup($("#vm_"+vmID+" .vm_name")[0].innerHTML+" : "+taskDetail.command,taskID);
		}
		else	//Finish
		{
			//alert("remove"+taskID)
			viid = getVIOwner(vmID,"id");
			checkActivityOnce(vmID)	;
			//removePopup(taskID);
			$("#vm_vmcanControl_"+vmID).text("free") ;
			if(taskDetail.command == "guest_destroy"){
				vCPU = parseInt($("#vm_vCPU_"+vmID).text());
				ram = parseInt($("#vm__memory"+vmID).text())/256;
				setUsedQouta(viid,-1,-vCPU,-ram);
				$("div#vm_"+vmID).fadeOut(300, function() { $(this).remove(); });
				checkDisableCreateVMBttn(viid);
			}
			if (taskDetail.command == "guest_create"){
					$("#vm_progress_"+vmID).hide();
			}
			refreshLog(viid)
		}
		toggleVMWait(vmID);
	}
	else{
		//popAlert(res.responseText);
	}
}