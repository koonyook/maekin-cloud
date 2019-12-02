function addWrap(content,enlarge){
		//$("#wrapup").addClass("wrap-black"); 
		$("#wrapup").show()
		content.show(); 
		content.addClass("wrap_content");
		$("#wrap_div").append(content);
		if(enlarge != 0){
			$("#wrap_div").attr("style","margin :"+enlarge+"% auto;")
		}
		$("#wrap_div").show();
		return false; 
	}
function removeWrap(){
	$("#wrapup").hide()
	//$("#wrapup").removeClass("wrap-black");
	//$("#wrapup").removeClass("wrap-white");
	$("#wrap_div").hide();
	$(".bttn_vm_advance").removeClass("bttn_vm_overlay_ch");
	$(".bttn_vm_advance").removeClass("bttn_vm_advance_disable");
	$(".bttn_vm_advance").unbind();
	$("#wrap_div").children().not("#wrap_close").hide();
	$("#wrap_pool").append($("#wrap_div").children().not("#wrap_close"));
	stopPollGraph();
}
function alertSetup(text,funcOK,funcCancel){
	$("#alert_text").text(text);
	addWrap($("#vi_alert"),10);
	$("#alert_OK").unbind();
	$("#alert_cancel").unbind();
	$("#alert_OK").click(funcOK);
	$("#alert_cancel").click(funcCancel);
}
function errorSetup(text){
	$("#alert_text").text(text);
	addWrap($("#vi_alert"),10);
	$("#alert_OK").unbind();
	$("#alert_OK").click(function(){removeWrap();});
	$("#alert_cancel").hide();
}