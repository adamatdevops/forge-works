package forgeworks

// ForgeWorks Canonical Schema Library
// This is the SINGLE SOURCE OF TRUTH for all data contracts.
// JSON Schemas are generated from this file in CI.

// ============================================================
// Base types — canonical numeric units for cross-tool comparison
// ============================================================

#Resources: {
	cpu_millicores: int & >=0  // K8s "250m"→250, "1"→1000, Terraform cpu=256→250
	memory_mib:     int & >=0  // K8s "512Mi"→512, "2Gi"→2048, Terraform memory=512→512
	storage_gib?:   int & >=0  // Optional storage
}

#Labels: [string]: string

#Source: "kubernetes" | "terraform" | "github-actions" | "argocd" | "helm"

// ============================================================
// #Workload — unified compute definition
// ============================================================
// Maps to: K8s Deployment/StatefulSet, Terraform ECS Task, Docker Compose service

#Workload: {
	name:      string
	namespace: string | *"default"
	replicas:  int & >=0
	image:     string | *""
	resources: #Resources
	labels:    #Labels
	source:    #Source

	// Health
	healthy:     bool | *true
	ready:       bool | *true
	crash_loops: int & >=0 | *0

	// Probes
	has_liveness_probe:  bool | *false
	has_readiness_probe: bool | *false

	// Scaling
	hpa?: {
		minReplicas: int & >=1
		maxReplicas: int & >=1
		targetCPU:   int & >=1 & <=100 // percentage
	}
}

// ============================================================
// #Service — unified network exposure
// ============================================================
// Maps to: K8s Service, Terraform ALB/NLB, Cloud Run service

#Service: {
	name:      string
	namespace: string | *"default"
	port:      int & >0 & <=65535
	protocol:  "TCP" | "UDP" | *"TCP"
	type:      "ClusterIP" | "LoadBalancer" | "NodePort" | *"ClusterIP"
	selector:  #Labels
	source:    #Source
}

// ============================================================
// #Pipeline — unified CI/CD definition
// ============================================================
// Maps to: GitHub Actions workflow, GitLab CI, Jenkins pipeline

#Pipeline: {
	name:       string
	repository: string
	trigger:    [...string] // ["push", "pull_request"]
	stages:     [...#Stage]
	source:     #Source
}

#Stage: {
	name:       string
	image:      string | *""
	steps:      [...string]
	depends:    [...string] | *[]
	status:     "" | "queued" | "in_progress" | "completed" | *""
	conclusion: "" | "success" | "failure" | "cancelled" | "skipped" | *""
}

// ============================================================
// #Deployment — unified GitOps definition
// ============================================================
// Maps to: ArgoCD Application, Flux Kustomization

#Deployment: {
	name:        string
	namespace:   string | *"default"
	source_repo: string
	source_path: string
	target:      string // cluster/namespace
	sync_status: "Synced" | "OutOfSync" | "Unknown" | *"Unknown"
	health:      "Healthy" | "Degraded" | "Missing" | "Unknown" | *"Unknown"
	auto_sync:   bool | *false
	source:      #Source
}

// ============================================================
// #NormalizedConfig — wrapper with metadata
// ============================================================

#NormalizedConfig: {
	config_id:      string
	resource_ref:   string // join key: "{source}:{namespace}/{name}" or "{source}:{repo}"
	schema_version: int & >=2
	observed_at:    string // ISO 8601
	source:         #Source
	resource_type:  "workload" | "service" | "pipeline" | "deployment"
	resource:       #Workload | #Service | #Pipeline | #Deployment
	raw_hash:       string // SHA256 of original input
}
