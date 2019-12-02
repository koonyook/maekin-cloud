function getID(a){
	return a.attr('id').split('_')[a.attr('id').split('_').length - 1]
}
function toggleVIMenu(viid,classbttn){
	if(classbttn.indexOf("vi_menu_select") < 0){
		$("#vi_menu_tab_"+viid+" a").removeClass("vi_menu_select");
		if(classbttn == 'vi_menu_vm_bttn'){
			$("#vm_vi_"+viid).show();
			$("#vi_summary_form_"+viid).hide();
			$("#vi_template_form_"+viid).hide();
			$("#vi_user_form_"+viid).hide();
			$("#vi_menu_vm_bttn_"+viid).addClass("vi_menu_select");
		}
		
		else if(classbttn == 'vi_menu_template_bttn'){
			$("#vm_vi_"+viid).hide();
			$("#vi_summary_form_"+viid).hide();
			$("#vi_template_form_"+viid).show();
			$("#vi_user_form_"+viid).hide();
			$("#vi_menu_template_bttn_"+viid).addClass("vi_menu_select");
		}
		else if(classbttn == 'vi_menu_user_bttn'){
			$("#vm_vi_"+viid).hide();
			$("#vi_summary_form_"+viid).hide();
			$("#vi_template_form_"+viid).hide();
			$("#vi_user_form_"+viid).show();
			$("#vi_menu_user_bttn_"+viid).addClass("vi_menu_select");
		}
		else if(classbttn == 'vi_menu_summary_bttn'){
			$("#vm_vi_"+viid).hide();
			$("#vi_summary_form_"+viid).show();
			$("#vi_template_form_"+viid).hide();
			$("#vi_user_form_"+viid).hide();
			$("#vi_menu_summary_bttn_"+viid).addClass("vi_menu_select");
		}
	}
}
function changeURL(newURL){
		var stateObj = "token"
		history.pushState(stateObj, "changeFocusMenu",newURL);
	}
function removeUserFromRole(){
	viid =  $(this).parent().attr("id").split("_")[2];
	old_roleid = $(this).parent().attr("id").split("_")[3];
	userid = $(this).parent().attr("id").split("_")[4];
	//alert(viid+old_roleid+userid)
	//$(this).parent().parent().attr("id").split("")
	username = $(this).parent().children(".role_user_name").text();
	//username = $("#user_object_name_"+viid+"_"+old_roleid+"_"+userid).text();
	rolename = $("#vi_role_name_"+old_roleid).text();
	askText = "Remove " + username + " from role " + rolename;
	alertSetup(askText,
		function(){
			postBack("/moveUser",{userid:userid,old_roleid:old_roleid,viid:viid,com:'remove'},function(data){
				if(data.responseText == "clear"){
					$("#user_object_"+viid+"_"+old_roleid+"_"+userid).addClass("user_object_left");
					$("#user_object_"+viid+"_"+old_roleid+"_"+userid).removeClass("user_object");
					$("#user_object_"+viid+"_"+old_roleid+"_"+userid).children(".removeUserBttn").hide()
					$("#user_object_"+viid+"_"+old_roleid+"_"+userid)[0].id = "user_object_"+viid+"_left_"+userid;
					$("#vi_role_userleft_"+viid).append($("#user_object_"+viid+"_left_"+userid))
				}
				else{
					popAlert(data.responseText);
					return false;
				}
			})
			removeWrap();
		},
		function(){
			removeWrap();
		}
	)
	return false;
}
function setMoveUser(res,status){
	//alert(res.responseText);
	data = jQuery.parseJSON(res.responseText)
	if($("#vi_role_userleft_"+data.viid).is(":visible")){
		$("#vi_role_data_"+data.viid).children(".user_left_pool").children(".user_object_left").draggable({containment: "#vi_role_data_"+data.viid,revert:"invalid",handle:".role_user_name",helper:"clone"})
		$("#vi_role_data_"+data.viid).children(".user_left_pool").children(".user_object_left").children(".role_user_name").addClass("haveMove");
		for(var i = 0; i < data.canAdd.length; i++){
			$("#vi_role_user_"+data.canAdd[i]).children(".user_object").not(".user_cloudadmin").draggable({containment: "#vi_role_data_"+data.viid,revert:"invalid",handle:".role_user_name",helper:"clone"})
			$("#vi_role_user_"+data.canAdd[i]).children(".user_object").children(".role_user_name").not(".role_user_cloudadmin").addClass("haveMove");
		}
		for(var i = 0; i < data.canDelete.length; i++){
			$("#vi_role_user_"+data.canDelete[i]).children(".user_object").children(".removeUserBttn").toggle();
		}
		$(".user_pool").droppable({hoverClass:"pool_targeted",greedy: true,accept:".user_object,.user_object_left",drop:function(event,ui){
				roleid = $(this).attr("id").split("_")[3]
				if (ui.draggable.hasClass("user_object_left")){
					userid = ui.draggable.attr("id").split("_")[4]
					viid = ui.draggable.attr("id").split("_")[2]
					postBack("/moveUser",{userid:userid,roleid:roleid,viid:viid,com:'add'},function(data){
						if(data.responseText == "clear"){
							ui.draggable.removeClass("user_object_left");
							ui.draggable.addClass("user_object");
							if (ui.draggable.children("a").length < 1)
								ui.draggable.prepend('<a class="removeUserBttn" href="#">X </a>');
							else
								ui.draggable.children("a").show();
							$("#vi_role_user_"+roleid).append(ui.draggable)
							ui.draggable.attr("id","user_object_"+viid+"_"+roleid+"_"+userid)
							$(".removeUserBttn").unbind()
							$(".removeUserBttn").click(removeUserFromRole)
						}
						else{
							popAlert(data.responseText);
							return false;
						}
					})
				}
				else{
					viid =  ui.draggable.attr("id").split("_")[2];
					old_roleid = ui.draggable.attr("id").split("_")[3];
					userid = ui.draggable.attr("id").split("_")[4];
					//alert(old_roleid+viid+userid);
					if (old_roleid== roleid)
						return false;
					postBack("/moveUser",{userid:userid,old_roleid:old_roleid,roleid:roleid,viid:viid,com:'move'},function(data){
						if(data.responseText == "clear"){
							ui.draggable[0].id = "user_object_"+viid+"_"+roleid+"_"+userid;
							$("#vi_role_user_"+roleid).append(ui.draggable)
						}
						else{
							errorSetup(data.responseText);
							return false;
						}
					})
				}
			}
		});
	}
	else{
		$("#vi_role_data_"+data.viid).children(".user_left_pool").children(".user_object_left").removeClass("ui-draggable")
		$("#vi_role_data_"+data.viid).children(".user_left_pool").children(".user_object_left").children(".role_user_name").removeClass("haveMove");
		for(var i = 0; i < data.canAdd.length; i++){
			$("#vi_role_user_"+data.canAdd[i]).children(".user_object").removeClass("ui-draggable")
			$("#vi_role_user_"+data.canAdd[i]).children(".user_object").children(".role_user_name").removeClass("haveMove");
		}
		for(var i = 0; i < data.canDelete.length; i++){
			$("#vi_role_user_"+data.canDelete[i]).children(".user_object").children(".removeUserBttn").toggle();
		}
	}
}
//////////////////////////////////////
// Check for move role user
///////////////////////////////////////
function checkChangeUser(userid,roleid){
	//alert(userid+"fdf"+roleid)
	postBack("/moveUser",{userid:userid,roleid:roleid,com:"add"},function(data){
		//alert(data.responseText);
		if(data.responseText != "clear")
			popAlert(data.responseText);
		else{
			$("#vi_role_user_"+roleid).append($("#user_object_"+roleid+"_left_"+userid))
		}
	})
}