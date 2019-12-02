function getCookie(c_name)
{
        if (document.cookie.length > 0)
        {
            c_start = document.cookie.indexOf(c_name + "=");
            if (c_start != -1)
            {
                c_start = c_start + c_name.length + 1;
                c_end = document.cookie.indexOf(";", c_start);
                if (c_end == -1) c_end = document.cookie.length;
                return unescape(document.cookie.substring(c_start,c_end));
            }
        }
        return "";
}
function postBack(url,dataSend,completefunc)
	{
		var data = dataSend;
		var args = {type:"POST",url:url,data:data,complete:function(res,status){
			//alert(">>"+res.responseText+"<<")
			if(res.responseText == ""){
				completefunc(res,'error')
			}
			else
				completefunc(res,status)
			}
		};
		$.ajaxSetup({headers: { "X-CSRFToken": getCookie("csrftoken") }});
		$.ajax(args)
}
function getID(a){
			return a.attr('id').split('_')[a.attr('id').split('_').length - 1]
}
function popAlert(text){
		var caller_name = arguments.callee.caller.toString();
		text = "<b>Alert From:</b><br/>"+caller_name+"<br/><br/><br/>"+text;
		var recipe =  window.open('','RecipeWindow','width=600,height=600');
		recipe.document.open();
		recipe.document.write(text);
		recipe.document.close();
}
function isValidEmailAddress(emailAddress) {
    var pattern = new RegExp(/^(("[\w-+\s]+")|([\w-+]+(?:\.[\w-+]+)*)|("[\w-+\s]+")([\w-+]+(?:\.[\w-+]+)*))(@((?:[\w-+]+\.)*\w[\w-+]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?)$)|(@\[?((25[0-5]\.|2[0-4][\d]\.|1[\d]{2}\.|[\d]{1,2}\.))((25[0-5]|2[0-4][\d]|1[\d]{2}|[\d]{1,2})\.){2}(25[0-5]|2[0-4][\d]|1[\d]{2}|[\d]{1,2})\]?$)/i);
    return pattern.test(emailAddress);
};
function checkIsNumber(){
	var inp = $(this).val();
	var checkNumberorChar = /^[a-zA-Z0-9]*$/.test(inp);
}
function isCharAndNumber(inp){
	var  test = /^[a-zA-Z0-9]*$/.test(inp);
	return test
}
function isNumber(inp){
	var test = /^[0-9]*$/.test(inp);
	return test
}
function isCharNumberAndUnderscore(inp){
	var test = /^[0-9a-zA-Z_]*$/.test(inp);
	return test;
}
function isIP(inp){
	var test = /^(\d+\.){3}\d+/.test(inp);
	return test;
}
function isMAC(){
	var test = /^([\dABCDEF]{2}:){5}[\dABCDEF]{2}/.test(inp);
	return test;
}