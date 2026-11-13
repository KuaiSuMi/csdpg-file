#include "config.pml"

#include "/opt/kivi/kivi/templates/include.pml"

#include "event.pml"

#include "intentsCheck.pml"

init{
	podTemplates[1].cpuRequested = 100; 
podTemplates[1].topoSpreadConstraints[0].maxSkew = 2; 
podTemplates[1].topoSpreadConstraints[0].topologyKey = 0; 
podTemplates[1].topoSpreadConstraints[0].whenUnsatisfiable = 0; 
podTemplates[1].topoSpreadConstraints[0].nodeAffinityPolicy = 1; 
podTemplates[1].topoSpreadConstraints[0].nodeTaintsPolicy = 0; 
podTemplates[1].topoSpreadConstraints[0].minDomains = 1; 
podTemplates[1].topoSpreadConstraints[0].numMatchedLabel = 1; 
podTemplates[1].topoSpreadConstraints[0].labelKey[0] = 2; 
podTemplates[1].topoSpreadConstraints[0].labelValue[0] = 1; 
podTemplates[1].topoSpreadConstraints[1].maxSkew = 1; 
podTemplates[1].topoSpreadConstraints[1].topologyKey = 1; 
podTemplates[1].topoSpreadConstraints[1].whenUnsatisfiable = 0; 
podTemplates[1].topoSpreadConstraints[1].nodeAffinityPolicy = 1; 
podTemplates[1].topoSpreadConstraints[1].nodeTaintsPolicy = 0; 
podTemplates[1].topoSpreadConstraints[1].minDomains = 1; 
podTemplates[1].topoSpreadConstraints[1].numMatchedLabel = 1; 
podTemplates[1].topoSpreadConstraints[1].labelKey[0] = 2; 
podTemplates[1].topoSpreadConstraints[1].labelValue[0] = 1; 
podTemplates[1].numTopoSpreadConstraints = 2; 
podTemplates[1].memRequested = 0; 
podTemplates[1].numRules = 0; 
podTemplates[1].nodeName = 0; 
podTemplates[1].maxCpuChange = 0; 
podTemplates[1].labelKeyValue[0] = 0; 
podTemplates[1].labelKeyValue[1] = 0; 
podTemplates[1].labelKeyValue[2] = 1; 
d[1].name = 3; 
d[1].specReplicas = 5; 
d[1].podTemplateId = 1; 
d[1].hpaSpec.isEnabled = 1; 
d[1].hpaSpec.metricTypes[0] = 1; 
d[1].hpaSpec.metricNames[0] = 0; 
d[1].hpaSpec.metricTargets[0] = 50; 
d[1].hpaSpec.numMetrics = 1; 
d[1].hpaSpec.maxReplicas = 6; 
d[1].hpaSpec.minReplicas = 1; 
d[1].status = 0; 
d[1].replicaSets[0].specReplicas = 5; 
d[1].replicaSets[0].version = 0; 
d[1].replicas = 0; 
d[1].curVersion = 0; 
d[1].maxSurge = 25; 
d[1].maxUnavailable = 25; 
d[1].strategy = 0; 
nodes[1].cpu = 24000; 
nodes[1].memory = 63; 
nodes[1].cpuLeft = 24000; 
nodes[1].memLeft = 63; 
nodes[1].status = 1; 
nodes[1].maintained = 0; 
nodes[2].cpu = 24000; 
nodes[2].memory = 63; 
nodes[2].cpuLeft = 24000; 
nodes[2].memLeft = 63; 
nodes[2].status = 1; 
nodes[2].maintained = 0; 
nodes[3].cpu = 24000; 
nodes[3].memory = 63; 
nodes[3].cpuLeft = 24000; 
nodes[3].memLeft = 63; 
nodes[3].status = 1; 
nodes[3].maintained = 0; 
pods[1].status = 0; 
pods[1].loc = 0; 
pods[1].workloadType = 0; 
pods[1].workloadId = 0; 
pods[1].podTemplateId = 0; 
pods[1].curCpuIndex = 1; 
pods[1].startTime = 0; 
pods[2].status = 0; 
pods[2].loc = 0; 
pods[2].workloadType = 0; 
pods[2].workloadId = 0; 
pods[2].podTemplateId = 0; 
pods[2].curCpuIndex = 1; 
pods[2].startTime = 0; 
pods[3].status = 0; 
pods[3].loc = 0; 
pods[3].workloadType = 0; 
pods[3].workloadId = 0; 
pods[3].podTemplateId = 0; 
pods[3].curCpuIndex = 1; 
pods[3].startTime = 0; 
pods[4].status = 0; 
pods[4].loc = 0; 
pods[4].workloadType = 0; 
pods[4].workloadId = 0; 
pods[4].podTemplateId = 0; 
pods[4].curCpuIndex = 1; 
pods[4].startTime = 0; 
pods[5].status = 0; 
pods[5].loc = 0; 
pods[5].workloadType = 0; 
pods[5].workloadId = 0; 
pods[5].podTemplateId = 0; 
pods[5].curCpuIndex = 1; 
pods[5].startTime = 0; 
pods[6].status = 0; 
pods[6].loc = 0; 
pods[6].workloadType = 0; 
pods[6].workloadId = 0; 
pods[6].podTemplateId = 0; 
pods[6].curCpuIndex = 1; 
pods[6].startTime = 0; 
pods[7].status = 0; 
pods[7].loc = 0; 
pods[7].workloadType = 0; 
pods[7].workloadId = 0; 
pods[7].podTemplateId = 0; 
pods[7].curCpuIndex = 1; 
pods[7].startTime = 0; 
pods[8].status = 0; 
pods[8].loc = 0; 
pods[8].workloadType = 0; 
pods[8].workloadId = 0; 
pods[8].podTemplateId = 0; 
pods[8].curCpuIndex = 1; 
pods[8].startTime = 0; 
pods[9].status = 0; 
pods[9].loc = 0; 
pods[9].workloadType = 0; 
pods[9].workloadId = 0; 
pods[9].podTemplateId = 0; 
pods[9].curCpuIndex = 1; 
pods[9].startTime = 0; 
nodesStable[1].name = 0; 
nodesStable[1].score = 0; 
nodesStable[1].curScore = 0; 
nodesStable[1].curAffinity = 0; 
nodesStable[1].curTaint = 0; 
nodesStable[1].labelKeyValue[0] = 1; 
nodesStable[1].labelKeyValue[1] = 1; 
nodesStable[1].labelKeyValue[2] = 0; 
nodesStable[2].name = 1; 
nodesStable[2].score = 0; 
nodesStable[2].curScore = 0; 
nodesStable[2].curAffinity = 0; 
nodesStable[2].curTaint = 0; 
nodesStable[2].labelKeyValue[0] = 1; 
nodesStable[2].labelKeyValue[1] = 2; 
nodesStable[2].labelKeyValue[2] = 0; 
nodesStable[3].name = 2; 
nodesStable[3].score = 0; 
nodesStable[3].curScore = 0; 
nodesStable[3].curAffinity = 0; 
nodesStable[3].curTaint = 0; 
nodesStable[3].labelKeyValue[0] = 2; 
nodesStable[3].labelKeyValue[1] = 3; 
nodesStable[3].labelKeyValue[2] = 0; 
podsStable[1].cpu = 0; 
podsStable[1].memory = 0; 
podsStable[1].score = 0; 
podsStable[1].important = 0; 
podsStable[2].cpu = 0; 
podsStable[2].memory = 0; 
podsStable[2].score = 0; 
podsStable[2].important = 0; 
podsStable[3].cpu = 0; 
podsStable[3].memory = 0; 
podsStable[3].score = 0; 
podsStable[3].important = 0; 
podsStable[4].cpu = 0; 
podsStable[4].memory = 0; 
podsStable[4].score = 0; 
podsStable[4].important = 0; 
podsStable[5].cpu = 0; 
podsStable[5].memory = 0; 
podsStable[5].score = 0; 
podsStable[5].important = 0; 
podsStable[6].cpu = 0; 
podsStable[6].memory = 0; 
podsStable[6].score = 0; 
podsStable[6].important = 0; 
podsStable[7].cpu = 0; 
podsStable[7].memory = 0; 
podsStable[7].score = 0; 
podsStable[7].important = 0; 
podsStable[8].cpu = 0; 
podsStable[8].memory = 0; 
podsStable[8].score = 0; 
podsStable[8].important = 0; 
podsStable[9].cpu = 0; 
podsStable[9].memory = 0; 
podsStable[9].score = 0; 
podsStable[9].important = 0; 


	// init finished
	init_status = 1
	short i = 0;

	first_proc = 0;
	first_proc = 1;

	if
		:: first_proc == 1 ->
			run deploymentController();
			run scheduler();
			#ifdef HPA_ENABLED
			run hpa();
			#endif
			run nodeController();
			run kubelet();

			run eventCpuChange(1) 
run createTargetDeployment(1) 

			
			

			// for (i : 1 .. NODE_NUM) {
			// 	run podCpuChangeWithPattern(i);
			// }

			// run podCpuChangeWithPattern()

			// TODO: check on if the order of running the following actually matter or not
			// Intent check for H1
			// run checkH1();

			

			

			for (i : 1 .. DEP_NUM) {
				#ifdef HPA_ENABLED
				updateQueue(hpaQueue, hpaTail, hpaIndex, i, MAX_HPA_QUEUE);
				#endif
				updateQueue(dsQueue, dsTail, dsIndex, i, MAX_DESCHEDULER_QUEUE);
			}

endINIT:	if 
				:: (ncIndex == ncTail && hpaTail == hpaIndex && sIndex == sTail && kblIndex == kblTail && dcIndex == dcTail) ->
					
					skip
			fi;
	fi
}