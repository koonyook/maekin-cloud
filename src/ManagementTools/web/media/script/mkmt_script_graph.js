var monitoringRequest = false;
var monitoringInterval = 800;
function stopPollGraph(){
	monitoringRequest = false;
}
function pollStatGraph(targetID,isVM,isRun,graphCPU,graphMEM,graphNET,graphIO){
	monitoringRequest = true;
	var cpuList = [];
	var memList = [];
	var netReceive = [];
	var netSend = [];
	var ioList  = [];
	var polltype;
	if (isVM){
		polltype = "vm";
		var totalPoints = $("#"+polltype+"_graph_cpu").width()/2.5;
	}
	else{
		polltype = "host";
		var totalPoints = $("#"+graphCPU).width()/2.5;
		//alert(graphCPU+""+graphMEM+""+graphNET+""+graphIO);
	}
	
	for (var i = 0; i < totalPoints; ++i){
		cpuList[i] = 0;
		memList[i] = 0;
		netReceive[i] = 0;
		netSend[i] = 0;
		ioList[i] = 0;
	} 
	var cpuMax =5;
	var memMax=100;
	var netMax=0.1;
	var ioMax=100;
	 var options_cpu = {
		axesDefaults: {
        tickRenderer: $.jqplot.CanvasAxisTickRenderer ,
        tickOptions: {
          angle: -30,
          fontSize: '10pt',
		}
		},
		 axes: {
			xaxis: {
				min:0,
				showTicks:false ,
				showTickMarks: false,
				label:'CPU (% Average)',
				labelRenderer: $.jqplot.CanvasAxisLabelRenderer,
				labelOptions: {
					fontSize: '10pt'
				}
				},
			yaxis:{
				min:0,
				max:100,tickOptions: {formatString:'%d'},numberTicks:2
				}
			},
		seriesDefaults:{showMarker:false,shadow:false}
		};
 	 var options_mem = {
		axesDefaults: {
        tickRenderer: $.jqplot.CanvasAxisTickRenderer ,
        tickOptions: {
          angle: -30,
          fontSize: '10pt',
		}
		},
		 axes: {
			xaxis: {min:0,show:false,showTicks:false,showTickMarks: false ,				
				label:'MEM (% Used)',
				labelRenderer: $.jqplot.CanvasAxisLabelRenderer,
				labelOptions: {
					fontSize: '10pt'
				}},
			yaxis:{min:0,max:100,tickOptions: {formatString:'%d'},numberTicks:2
				}
			},
		seriesDefaults:{showMarker:false,shadow:false}
		};
	 var options_net = {
		axesDefaults: {
        tickRenderer: $.jqplot.CanvasAxisTickRenderer ,
        tickOptions: {
          angle: -30,
          fontSize: '10pt'
		}
		},
		 axes: {
			xaxis: {min:0,showTicks:false,showTickMarks: false ,				
				label:'NETWORK (MB/s)',
				labelRenderer: $.jqplot.CanvasAxisLabelRenderer,
				labelOptions: {
					fontSize: '10pt'
				}},
			yaxis:{min:0,tickOptions: {formatString:'%5.2f'},numberTicks:2
				}
			},
		seriesDefaults:{showMarker:false,shadow:false}
		};
		var options_io = {
		axesDefaults: {
        tickRenderer: $.jqplot.CanvasAxisTickRenderer ,
        tickOptions: {
          angle: -30,
          fontSize: '10pt'
		}
		},
		 axes: {
			xaxis: {min:0,showTicks:false,showTickMarks: false ,				
				label:'IO (MB/s)',
				labelRenderer: $.jqplot.CanvasAxisLabelRenderer,
				labelOptions: {
					fontSize: '10pt'
				}},
			yaxis:{min:0,tickOptions: {formatString:'%5.2f'},numberTicks:2
				}
			},
		seriesDefaults:{showMarker:false,shadow:false}
		};
	 var options_storage = {
		axesDefaults: {
        tickRenderer: $.jqplot.CanvasAxisTickRenderer ,
        tickOptions: {
          angle: -30,
          fontSize: '10pt'
		}
		},
		 axes: {
			xaxis: {min:0,showTicks:false,showTickMarks: false ,				
				label:'Storage (% Used)',
				labelRenderer: $.jqplot.CanvasAxisLabelRenderer,
				labelOptions: {
					fontSize: '10pt'
				}},
			yaxis:{min:0,max:100,tickOptions: {formatString:'%5.2f'},numberTicks:2
				}
			},
		seriesDefaults:{showMarker:false,shadow:false}
		};
	//var plot_cpu = $.jqplot(graphCPU, [genGraphData(cpuList)] );
	//var plot_mem = $.$.jqplot($("#"+graphMEM), [genGraphData(memList)], options_mem);
	//var plot_net = $.jqplot(graphNET, [genGraphData(netReceive)] );
	//var plot_io = $.jqplot(graphIO, [genGraphData(ioList)] ); 
	function genGraphData(dataList){
		var debug = "";
		var res = [];
		for (var i = 0; i < totalPoints; ++i){
            res.push([i, dataList[i]]);
			debug = debug +">"+ i+":"+dataList[i] + '<br/>'
		}
		//popAlert(debug);
		return res;
		
	}
	function extractVMData(res,status){
		if(status == "success"){
			data = jQuery.parseJSON(res.responseText);
			vmstat =  data[0];
			 if (cpuList.length == totalPoints){
				cpuList = cpuList.slice(1);
				memList = memList.slice(1);
				netReceive = netReceive.slice(1);
				netSend = netSend.slice(1);
				ioList = ioList.slice(1);
			}
			cpuData = parseFloat(vmstat.cpuAverage);
			memData = vmstat.memTotal == '0' ? 0 : vmstat.memUse/vmstat.memTotal*100;
			netReceiveData = parseFloat(vmstat.netRX)/128000;
			netSendData = parseFloat(vmstat.netTX)/128000;
			ioData = (parseFloat(vmstat.ioRX)+parseFloat(vmstat.ioTX))/1024000000;
			//popAlert(cpuData+","+memData+","+netData+","+ioData+",");
			cpuList.push(cpuData);
			memList.push(memData);
			netReceive.push(netReceiveData);
			netSend.push(netSendData);
			ioList.push(ioData);
		}
	}
	function extractHostData(res,status){
		if(status == "success"){
			data = jQuery.parseJSON(res.responseText);
			hoststat =  data[0];
			lastCPUInfo = cpuList[cpuList.length-1]
			lastMemInfo = cpuList[cpuList.length-1]
			lastNetInfo = cpuList[cpuList.length-1]
			lastIOInfo = cpuList[cpuList.length-1]
			 if (cpuList.length == totalPoints){
				cpuList = cpuList.slice(1);
				memList = memList.slice(1);
				netReceive = netReceive.slice(1);
				netSend = netSend.slice(1);
				ioList = ioList.slice(1);
			}
			cpuData = hoststat.cpuAverage == '-' ? lastCPUInfo : 
				parseFloat(hoststat.cpuAverage);
			memData = hoststat.memTotal == '-' || hoststat.memFree == '-' ? lastMemInfo : 
				(parseFloat(hoststat.memTotal)-parseFloat(hoststat.memFree))/parseFloat(hoststat.memTotal)*100;
			netReceiveData = hoststat.netRX == '-' ? lastNetInfo :parseFloat(hoststat.netRX)/128000;
			netSendData = hoststat.netTX == '-' ? lastNetInfo :parseFloat(hoststat.netTX)/128000;
			ioData = hoststat.storageFree == '-' ? lastIOInfo :
				(parseFloat(hoststat.storageCap)-parseFloat(hoststat.storageFree))/parseFloat(hoststat.storageCap)*100;
			cpuList.push(cpuData);
			memList.push(memData);
			netReceive.push(netReceiveData);
			netSend.push(netSendData);
			ioList.push(ioData);
		}
	}
	function updateGraph(){
		if(isRun){
			if(isVM){
				getvmInfo(targetID,1,1,1,1,extractVMData);
			}
			else{ //host graph
				gethostInfo(targetID,extractHostData);
			}
		}
		$("#"+graphCPU).empty();
		$("#"+graphNET).empty();
		$("#"+graphIO).empty();
		$.jqplot(graphCPU, [genGraphData(cpuList)],options_cpu);
		$.jqplot(graphNET, [genGraphData(netReceive),genGraphData(netSend)],options_net);
		if(!isVM){
			$("#"+graphMEM).empty();
			$.jqplot(graphMEM, [genGraphData(memList)],options_mem);
			$.jqplot(graphIO, [genGraphData(ioList)],options_storage);
		}
		else{
			$.jqplot(graphIO, [genGraphData(ioList)],options_io);
		}
		if(monitoringRequest && isRun)
			setTimeout(updateGraph, monitoringInterval);
	}
	updateGraph();
}