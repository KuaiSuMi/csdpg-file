
/*----------- k8s cluster setup ------------*/
//#define MAX_POD [$MAX_POD]
//#define MAX_NODE [$MAX_NODE]
//#define MAX_DEPLOYMENT [$MAX_DEPLOYMENT]
// Can't be more than 255
#define NODE_NUM 3
#define POD_NUM 9
#define DEP_NUM 1
// Will need to make it an variable if work for more namespaces.
#define NAMESPACE_NUM 1
#define POD_CPU_THRE 64
#define NODE_ALLOWED_POD_NUM 80
#define POD_TEMPLATE_NUM 1
#define DEP_TEMPLATE_NUM 0

// Propotional to the pods/nodes/deployments size
#define MAX_SCHEDULER_QUEUE 11
#define MAX_KUBELET_QUEUE 11
#define MAX_NODE_CONTROLLER_QUEUE 10
#define MAX_HPA_QUEUE 10
#define MAX_DEP_QUEUE 10
#define MAX_DESCHEDULER_QUEUE 11
#define MAX_TAINT_MANAGER_QUEUE 11
/*----------- deployment Config ------------*/

#define SlowStartInitialBatchSize 1


/*----------- scheduler Config ------------*/
// Both are enabled by default for the podSpreading plugins: https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/#topologyspreadconstraints-field
#define enableNodeInclusionPolicyInPodTopologySpread 1
#define enableMinDomainsInPodTopologySpread 1
// Because we have 2 default pod spreading policy, so this is true
#define systemDefaulted 1
#define userDefinedConstraints 1

// scheduler "internal" config, set for their default values. 
#define MAX_LABEL 4
#define MAX_VALUE 5
#define MAX_2D 5
// https://github.com/kubernetes/kubernetes/blob/c549b59983e114a872b0df18d74c1d217f3f62bd/pkg/scheduler/framework/interface.go#L109
#define MAX_NODE_SCORE 100


/*----------- hpa Config ------------*/

// HPA "internal" config, set for their default values. 

// default is 10 ( == 0.1 in percentage)
#define HPA_TOLERANCE 10

// These are default value defined in horizontal.go
#define HPA_SCALE_UP_LIMIT_MIN 4
#define HPA_SCALE_UP_LIMIT_FACTOR  2

/*----------- Array Config ------------*/
#define MAX_NUM_METRICS 1
#define MAX_NO_EXECUTE_NODE 1
#define MAX_NO_SCHEDULE_NODE 1
#define MAX_PEFER_NO_CHEDULE_NODE 1
#define MAX_TOPO_CON 2
#define MAX_AFFINITY_RULE 1
#define MAX_MATCHED_NODE 1
#define MAX_CPU_PATTERN 2


/*----------- Time Config ------------*/
// TODO: all the time can be config along with the event by the users
// 1 = 0.1s
#define HPA_RUN_TIME 1
#define HPA_WAIT_TIME 150
#define SCHEDULER_RUN_TIME 1
#define DEP_RUN_TIME 1
#define KUBELET_RUN_TIME 1
#define NODEC_RUN_TIME 1
#define MAINTENANCE_WAIT_TIME 600
#define KERNEL_RECOVER_TIME 600
#define EVENT_CPU_TIME 600
// Default descheduler interval is 5min
#define DESCHEDULER_WAIT_TIME 3000


/*--------- Descheduler Config -----------*/
#define maxNoOfPodsToEvictPerNode 5000
#define maxNoOfPodsToEvictPerNamespace 5000
#define MAX_NUM_DESPLUGINS 1
#define MAX_NUM_BALPLUGINS 1
#define MAX_NUM_EVICPLUGINS 1
// TBC for descheduler test
#define DES_PROFILE_NUM 1

/*--------- Event Config -----------*/
// TODO: this can be passed as a parameter by the users
#define EVENT_CPU_COUNT 1

/*--------- Intent Config -----------*/
#define LOOP_TIMES 3

/*--------- Internal Config -----------*/
#define UNDEFINED_VALUE -1

/*--------- optimization ------*/
// By default we don't look into the failures in transit (kubelet hence always run first than deployment).
// #define TRANSIT 1
#define BACK_TO_BACK_OPT 1

/*--------- ifdef ----------*/
// Intents: NO_FEASIBLE_NODE, 
// Data structure: MORE_PODS
#define HPA_ENABLED 1
#define NO_FEASIBLE_NODE 1
