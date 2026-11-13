#include "config.pml"

#include "/opt/kivi/kivi/templates/include.pml"

#include "event.pml"

#include "intentsCheck.pml"

init{
	nodes[1].cpu = 64; 
nodes[1].memory = 64; 
nodes[1].cpuLeft = 48; 
nodes[1].memLeft = 48; 
nodes[1].numPod = 2; 
nodes[1].status = 1; 
nodes[1].maintained = 0; 
nodes[2].cpu = 64; 
nodes[2].memory = 64; 
nodes[2].cpuLeft = 56; 
nodes[2].memLeft = 56; 
nodes[2].numPod = 1; 
nodes[2].status = 1; 
nodes[2].maintained = 0; 
nodes[3].cpu = 64; 
nodes[3].memory = 64; 
nodes[3].cpuLeft = 48; 
nodes[3].memLeft = 48; 
nodes[3].numPod = 2; 
nodes[3].status = 1; 
nodes[3].maintained = 0; 
pods[1].loc = 1; 
pods[1].workloadType = 1; 
pods[1].workloadId = 1; 
pods[1].podTemplateId = 1; 
pods[1].status = 1; 
pods[1].curCpuIndex = 1; 
pods[1].startTime = 0; 
pods[2].loc = 1; 
pods[2].workloadType = 1; 
pods[2].workloadId = 1; 
pods[2].podTemplateId = 1; 
pods[2].status = 1; 
pods[2].curCpuIndex = 1; 
pods[2].startTime = 0; 
pods[3].loc = 2; 
pods[3].workloadType = 1; 
pods[3].workloadId = 1; 
pods[3].podTemplateId = 1; 
pods[3].status = 1; 
pods[3].curCpuIndex = 1; 
pods[3].startTime = 0; 
pods[4].loc = 3; 
pods[4].workloadType = 1; 
pods[4].workloadId = 1; 
pods[4].podTemplateId = 1; 
pods[4].status = 1; 
pods[4].curCpuIndex = 1; 
pods[4].startTime = 0; 
pods[5].loc = 3; 
pods[5].workloadType = 1; 
pods[5].workloadId = 1; 
pods[5].podTemplateId = 1; 
pods[5].status = 1; 
pods[5].curCpuIndex = 1; 
pods[5].startTime = 0; 
pods[6].loc = 4; 
pods[6].workloadType = 1; 
pods[6].workloadId = 1; 
pods[6].podTemplateId = 1; 
pods[6].status = 0; 
pods[6].curCpuIndex = 1; 
pods[6].startTime = 0; 
d[1].name = 10; 
d[1].status = 1; 
d[1].curVersion = 0; 
d[1].replicaSets[0].deploymentId = 1; 
d[1].replicaSets[0].replicas = 5; 
d[1].replicaSets[0].specReplicas = 5; 
d[1].replicaSets[0].version = 0; 
d[1].replicaSets[0].podIds[0] = 1; 
d[1].replicaSets[0].podIds[1] = 2; 
d[1].replicaSets[0].podIds[2] = 3; 
d[1].replicaSets[0].podIds[3] = 4; 
d[1].replicaSets[0].podIds[4] = 5; 
d[1].replicaSets[1].deploymentId = 1; 
d[1].specReplicas = 5; 
d[1].replicas = 5; 
d[1].podTemplateId = 1; 
d[1].hpaSpec.isEnabled = 1; 
d[1].hpaSpec.numMetrics = 1; 
d[1].hpaSpec.metricNames[0] = 0; 
d[1].hpaSpec.metricTargets[0] = 91; 
d[1].hpaSpec.metricTypes[0] = 1; 
d[1].hpaSpec.minReplicas = 5; 
d[1].hpaSpec.maxReplicas = 6; 
d[1].maxSurge = 25; 
d[1].maxUnavailable = 25; 
d[1].strategy = 0; 
podTemplates[1].cpuRequested = 8; 
podTemplates[1].memRequested = 8; 
podTemplates[1].topoSpreadConstraints[0].maxSkew = 1; 
podTemplates[1].topoSpreadConstraints[0].topologyKey = 1; 
podTemplates[1].topoSpreadConstraints[0].whenUnsatisfiable = 0; 
podTemplates[1].topoSpreadConstraints[0].numMatchedLabel = 1; 
podTemplates[1].topoSpreadConstraints[0].nodeAffinityPolicy = 1; 
podTemplates[1].topoSpreadConstraints[0].nodeTaintsPolicy = 0; 
podTemplates[1].topoSpreadConstraints[0].minDomains = 1; 
podTemplates[1].topoSpreadConstraints[0].labelKey[0] = 2; 
podTemplates[1].topoSpreadConstraints[0].labelValue[0] = 1; 
podTemplates[1].numTopoSpreadConstraints = 1; 
podTemplates[1].numRules = 0; 
podTemplates[1].nodeName = 0; 
podTemplates[1].maxCpuChange = 0; 
podTemplates[1].labelKeyValue[0] = 0; 
podTemplates[1].labelKeyValue[1] = 0; 
podTemplates[1].labelKeyValue[2] = 1; 
nodesStable[1].name = 1; 
nodesStable[1].score = 0; 
nodesStable[1].curScore = 0; 
nodesStable[1].curAffinity = 0; 
nodesStable[1].curTaint = 0; 
nodesStable[1].labelKeyValue[0] = 1; 
nodesStable[1].labelKeyValue[1] = 1; 
nodesStable[1].labelKeyValue[2] = 0; 
nodesStable[2].name = 2; 
nodesStable[2].score = 0; 
nodesStable[2].curScore = 0; 
nodesStable[2].curAffinity = 0; 
nodesStable[2].curTaint = 0; 
nodesStable[2].labelKeyValue[0] = 1; 
nodesStable[2].labelKeyValue[1] = 2; 
nodesStable[2].labelKeyValue[2] = 0; 
nodesStable[3].name = 3; 
nodesStable[3].score = 0; 
nodesStable[3].curScore = 0; 
nodesStable[3].curAffinity = 0; 
nodesStable[3].curTaint = 0; 
nodesStable[3].labelKeyValue[0] = 2; 
nodesStable[3].labelKeyValue[1] = 3; 
nodesStable[3].labelKeyValue[2] = 0; 
podsStable[1].cpu = 8; 
podsStable[1].memory = 8; 
podsStable[1].important = 0; 
podsStable[1].score = 0; 
podsStable[1].labelKeyValue[0] = 0; 
podsStable[1].labelKeyValue[1] = 0; 
podsStable[1].labelKeyValue[2] = 1; 
podsStable[2].cpu = 8; 
podsStable[2].memory = 8; 
podsStable[2].important = 0; 
podsStable[2].score = 0; 
podsStable[2].labelKeyValue[0] = 0; 
podsStable[2].labelKeyValue[1] = 0; 
podsStable[2].labelKeyValue[2] = 1; 
podsStable[3].cpu = 8; 
podsStable[3].memory = 8; 
podsStable[3].important = 0; 
podsStable[3].score = 0; 
podsStable[3].labelKeyValue[0] = 0; 
podsStable[3].labelKeyValue[1] = 0; 
podsStable[3].labelKeyValue[2] = 1; 
podsStable[4].cpu = 8; 
podsStable[4].memory = 8; 
podsStable[4].important = 0; 
podsStable[4].score = 0; 
podsStable[4].labelKeyValue[0] = 0; 
podsStable[4].labelKeyValue[1] = 0; 
podsStable[4].labelKeyValue[2] = 1; 
podsStable[5].cpu = 8; 
podsStable[5].memory = 8; 
podsStable[5].important = 0; 
podsStable[5].score = 0; 
podsStable[5].labelKeyValue[0] = 0; 
podsStable[5].labelKeyValue[1] = 0; 
podsStable[5].labelKeyValue[2] = 1; 
podsStable[6].cpu = 8; 
podsStable[6].memory = 8; 
podsStable[6].important = 0; 
podsStable[6].score = 0; 


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
					run eventCpuChange(1) 

					skip
			fi;
	fi
}