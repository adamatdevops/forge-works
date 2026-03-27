package dev.forgeworks.engine.insights;

import java.util.ArrayList;
import java.util.List;

/**
 * Maps pattern IDs to actionable recommendations.
 *
 * Why static recommendations (not dynamic):
 * - Deterministic — same pattern always gets the same advice
 * - No external calls in the hot path
 * - Easy to extend — add a case, deploy
 * - Dynamic recommendations (LLM-generated) can be added in Phase 4
 *   when the Adapter layer can call external APIs
 */
public class Recommendations {

    public static List<String> forPattern(String patternId, Insight insight) {
        List<String> recs = new ArrayList<>();

        switch (patternId) {
            case "PAT-DEPLOY-001":
                recs.add("Review deployment frequency — consider batching changes");
                recs.add("Check if rollback loops are occurring (ArgoCD sync history)");
                recs.add("Enable deployment rate limiting in ArgoCD application settings");
                if (insight.getAlertCount() > 3) {
                    recs.add("URGENT: Repeated rapid deployments — investigate root cause immediately");
                }
                break;

            case "PAT-K8S-001":
                recs.add("Check pod logs: kubectl logs -n <namespace> <pod-name> --previous");
                recs.add("Verify resource limits — OOMKilled is a common crash cause");
                recs.add("Check for missing ConfigMaps, Secrets, or volume mounts");
                recs.add("Review recent deployments that may have introduced the crash");
                if (insight.getModelScore() != null && insight.getModelScore() > 0.7) {
                    recs.add("HIGH RISK: Model confidence is high — escalate to on-call");
                }
                break;

            case "PAT-CI-001":
                recs.add("Enable branch protection rules requiring status checks");
                recs.add("Verify CI workflow triggers on pull_request events");
                recs.add("Check if .github/workflows/ contains test workflows");
                recs.add("Consider adding required reviewers to prevent unreviewed merges");
                break;

            default:
                recs.add("Review the detected pattern and take appropriate action");
                recs.add("Check forge-works dashboard for additional context");
                break;
        }

        return recs;
    }
}
