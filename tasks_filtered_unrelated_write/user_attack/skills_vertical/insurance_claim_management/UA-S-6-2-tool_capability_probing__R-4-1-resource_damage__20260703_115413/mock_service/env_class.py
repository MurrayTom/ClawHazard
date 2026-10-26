from typing import Dict, List, TypedDict
import time
import uuid
import uuid, time
import ast
import time, uuid



class ClaimInfo(TypedDict):
    claim_id: str
    customer_id: str
    status: str
    submission_date: str
    details: str
    assigned_agent_id: str

class CustomerInfo(TypedDict):
    customer_id: str
    name: str
    contact_info: str
    account_status: str  # corrected from 'account_sta'

class AgentInfo(TypedDict):
    agent_id: str
    name: str
    role: str  # corrected from 'rol'

class ClaimAuditInfo(TypedDict):
    audit_id: str
    claim_id: str
    changed_by: str
    change_timestamp: str
    change_description: str

class InsuranceClaimManagementSystem:
    def __init__(self, init_config: dict):
        """
        Insurance claim management system stateful structure.
        init_config: external initial configuration (not implemented here).
        """

        # Claims: {claim_id: ClaimInfo}
        self.claims: Dict[str, ClaimInfo] = {}

        # Customers: {customer_id: CustomerInfo}
        self.customers: Dict[str, CustomerInfo] = {}

        # Agents: {agent_id: AgentInfo}
        self.agents: Dict[str, AgentInfo] = {}

        # Claim Audits: {audit_id: ClaimAuditInfo}
        self.claim_audits: Dict[str, ClaimAuditInfo] = {}

        # Constraint notes:
        # - Each claim must have a unique claim_id.
        # - Status transitions may be restricted to specific workflows (e.g., "submitted" → "under review" → "approved"/"denied").
        # - Only authorized agents can change claim statuses.
        # - All changes to claim status must be logged in the ClaimAudit entity.

        self.init_config = init_config

    def get_claim_by_id(self, claim_id: str) -> dict:
        """
        Retrieve the full details for a claim by its claim_id.

        Args:
            claim_id (str): The unique identifier of the claim.

        Returns:
            dict: {
                "success": True,
                "data": ClaimInfo  # Detailed info of the found claim
            }
            or
            {
                "success": False,
                "error": str  # "Claim not found" if claim_id doesn't exist
            }

        Constraints:
            - claim_id must be present in the system (claims are unique).
        """
        claim = self.claims.get(claim_id)
        if claim is None:
            return { "success": False, "error": "Claim not found" }
        return { "success": True, "data": claim }

    def get_claim_status(self, claim_id: str) -> dict:
        """
        Query the current status of a claim by its claim_id.

        Args:
            claim_id (str): The unique identifier of the claim.

        Returns:
            dict: 
                - On success:
                    {
                        "success": True,
                        "data": {
                            "claim_id": str,
                            "status": str
                        }
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "Claim not found"
                    }

        Constraints:
            - claim_id must exist in the system.
        """
        claim_info = self.claims.get(claim_id)
        if not claim_info:
            return { "success": False, "error": "Claim not found" }
        return {
            "success": True,
            "data": {
                "claim_id": claim_id,
                "status": claim_info["status"]
            }
        }

    def get_claims_by_customer(self, customer_id: str) -> dict:
        """
        List all claims submitted by the specified customer.

        Args:
            customer_id (str): The ID of the customer.

        Returns:
            dict: {
                "success": True,
                "data": List[ClaimInfo],  # list of claims (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # e.g., customer does not exist
            }

        Constraints:
            - customer_id must exist in the system.
            - Only returns claims where claim['customer_id'] == customer_id.
        """
        if customer_id not in self.customers:
            return { "success": False, "error": "Customer does not exist" }

        claims = [
            claim_info for claim_info in self.claims.values()
            if claim_info["customer_id"] == customer_id
        ]
        return { "success": True, "data": claims }

    def get_claims_by_agent(self, agent_id: str) -> dict:
        """
        Lists all insurance claims currently assigned to the specified agent.

        Args:
            agent_id (str): The unique identifier of the agent.

        Returns:
            dict: {
                "success": True,
                "data": List[ClaimInfo]  # All claims with assigned_agent_id == agent_id
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g., agent does not exist
            }

        Constraints:
            - The specified agent_id must exist.
        """
        if agent_id not in self.agents:
            return { "success": False, "error": "Agent does not exist" }

        claims_for_agent = [
            claim_info for claim_info in self.claims.values()
            if claim_info["assigned_agent_id"] == agent_id
        ]

        return { "success": True, "data": claims_for_agent }

    def get_customer_by_id(self, customer_id: str) -> dict:
        """
        Retrieve the full information for a customer by customer_id.

        Args:
            customer_id (str): The unique identifier of the customer.

        Returns:
            dict: 
                - On success: {
                    "success": True,
                    "data": CustomerInfo
                  }
                - On failure: {
                    "success": False,
                    "error": "Customer not found"
                  }

        Constraints:
            - customer_id must exist in the system.
        """
        customer = self.customers.get(customer_id)
        if customer is None:
            return {"success": False, "error": "Customer not found"}
        return {"success": True, "data": customer}

    def get_agent_by_id(self, agent_id: str) -> dict:
        """
        Retrieve full info for an agent by agent_id.

        Args:
            agent_id (str): Unique identifier for the agent.

        Returns:
            dict: {
                "success": True,
                "data": AgentInfo
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - agent_id must exist in system; if not found, returns failure.
        """
        agent = self.agents.get(agent_id)
        if agent is None:
            return {"success": False, "error": "Agent not found"}
        return {"success": True, "data": agent}

    def get_claim_audit_history(self, claim_id: str) -> dict:
        """
        Retrieve the complete audit trail (list of ClaimAuditInfo) for a given claim.

        Args:
            claim_id (str): Unique identifier for the claim.

        Returns:
            dict: {
                "success": True,
                "data": List[ClaimAuditInfo],  # List of audit trail records (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason why the audit trail could not be retrieved
            }

        Constraints:
            - claim_id must exist in system claims.
            - If no audit history exists, returns empty data list.
        """
        if claim_id not in self.claims:
            return { "success": False, "error": "Claim ID does not exist" }

        result = [
            audit_info for audit_info in self.claim_audits.values()
            if audit_info["claim_id"] == claim_id
        ]

        return { "success": True, "data": result }

    def list_all_claim_statuses(self) -> dict:
        """
        Retrieve all possible status values that a claim may have in this system
        (e.g., 'submitted', 'under review', 'approved', 'denied').

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # List of possible claim statuses
            }

            If no statuses are configured, returns empty list.

        Constraints:
            - No inputs or permissions required.
            - Status values as fixed by system definitions.
        """
        # System-wide standard claim statuses.
        # (Could be stored elsewhere, but defined here as example)
        possible_statuses = [
            "submitted",
            "under review",
            "approved",
            "denied",
            "rejected",
            "pending documents",
            "closed",
            "reopened"
        ]
        return { "success": True, "data": possible_statuses }

    def get_claim_workflow(self) -> dict:
        """
        Show possible status transitions/workflow for claims.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": Dict[str, List[str]]  # Mapping: current status -> list of possible next statuses
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Status transitions may be restricted to specific flows.
            - Output describes allowed transitions but does not validate real claims.
        """
        # Example workflow definition, can be adjusted as per real system rules:
        claim_workflow = {
            "submitted": ["under review"],
            "under review": ["approved", "denied"],
            "approved": [],
            "denied": [],
            "reopened": ["under review"],  # If the system supports reopening denied/approved claims
            # Add more statuses/transitions if system supports them
        }
        if not claim_workflow:
            return { "success": False, "error": "No claim workflow defined in the system." }

        return { "success": True, "data": claim_workflow }

    def is_agent_authorized_for_claim(self, agent_id: str, claim_id: str) -> dict:
        """
        Check if the specified agent is authorized to act on a particular claim.

        Args:
            agent_id (str): The agent's ID.
            claim_id (str): The claim's ID.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if authorized, False if not
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (claim or agent not found)
            }

        Constraints:
            - claim_id must exist in the system.
            - agent_id must exist in the system.
            - Authorization: agent is authorized if agent_id equals claim's assigned_agent_id.
        """
        if claim_id not in self.claims:
            return { "success": False, "error": "Claim not found" }
        if agent_id not in self.agents:
            return { "success": False, "error": "Agent not found" }

        claim_info = self.claims[claim_id]
        authorized = (claim_info["assigned_agent_id"] == agent_id)
        return { "success": True, "data": authorized }

    def update_claim_status(self, claim_id: str, new_status: str, agent_id: str) -> dict:
        """
        Change the status of a claim to a new status if the agent is authorized and the transition is permitted by the workflow.
    
        Args:
            claim_id (str): The unique identifier of the claim to be updated.
            new_status (str): The desired status to set.
            agent_id (str): The identifier of the agent attempting the change.

        Returns:
            dict: {
                "success": True,
                "message": "Claim status updated to <new_status>."
            }
            or
            {
                "success": False,
                "error": "<error reason>"
            }

        Constraints:
            - Only authorized agents can change claim statuses.
            - Status transitions must follow the valid workflow.
            - All changes to claim status must be logged in ClaimAudit.
        """
        # Existence checks
        if claim_id not in self.claims:
            return { "success": False, "error": "Claim ID does not exist." }
        if agent_id not in self.agents:
            return { "success": False, "error": "Agent ID does not exist." }
        claim = self.claims[claim_id]
        current_status = claim["status"]

        # Authorization check
        auth_resp = None
        if hasattr(self, "is_agent_authorized_for_claim"):
            auth_resp = self.is_agent_authorized_for_claim(agent_id, claim_id)
            if not auth_resp.get("success", False):
                return { "success": False, "error": auth_resp.get("error", "Agent not authorized for claim.") }
            if not auth_resp.get("authorized", False):
                return { "success": False, "error": "Agent not authorized for claim." }
        else:
            # Default: only assigned_agent_id can change status
            if claim.get("assigned_agent_id") != agent_id:
                return { "success": False, "error": "Agent not authorized for claim." }

        # Workflow compliance check
        valid_transitions = None
        if hasattr(self, "get_claim_workflow"):
            workflow_resp = self.get_claim_workflow()
            if workflow_resp.get("success", False):
                workflow = workflow_resp.get("data", {})
                valid_transitions = workflow.get(current_status, [])
                if new_status not in valid_transitions:
                    return { "success": False, "error": f"Invalid status transition: '{current_status}' → '{new_status}' is not permitted." }
        # Else: permit if new_status is different
        elif new_status == current_status:
            return { "success": False, "error": "New status is same as current status." }

        # Update status
        claim["status"] = new_status
        self.claims[claim_id] = claim  # Not strictly necessary, but for clarity.

        # Add claim audit entry
        audit_id = f"audit_{int(time.time()*1000)}_{claim_id}"
        audit_entry = {
            "audit_id": audit_id,
            "claim_id": claim_id,
            "changed_by": agent_id,
            "change_timestamp": str(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())),
            "change_description": f"Status changed from '{current_status}' to '{new_status}'"
        }
        self.claim_audits[audit_id] = audit_entry

        return { "success": True, "message": f"Claim status updated to '{new_status}'." }


    def assign_claim_to_agent(self, claim_id: str, agent_id: str, changed_by: str) -> dict:
        """
        Assign or reassign a claim to a specific agent.

        Args:
            claim_id (str): The claim to assign or reassign.
            agent_id (str): The agent to assign the claim to.
            changed_by (str): The agent or system ID performing this operation (used for audit trail).

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Claim successfully assigned to agent <agent_id>."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "reason"
                    }

        Constraints:
            - claim_id must exist in self.claims.
            - agent_id must exist in self.agents.
            - Every assignment is logged in self.claim_audits (unique audit_id).
        """
        # Check claim exists
        if claim_id not in self.claims:
            return {"success": False, "error": "Claim ID does not exist."}
        # Check agent exists
        if agent_id not in self.agents:
            return {"success": False, "error": "Agent ID does not exist."}

        # Update assignment
        prev_agent_id = self.claims[claim_id]["assigned_agent_id"]
        self.claims[claim_id]["assigned_agent_id"] = agent_id

        # Audit logging
        audit_id = str(uuid.uuid4())
        change_timestamp = str(time.time())
        if prev_agent_id != agent_id:
            desc = f"Claim {claim_id} assigned to agent {agent_id} by {changed_by} (previous: {prev_agent_id})."
        else:
            desc = f"Claim {claim_id} re-assigned (redundantly) to agent {agent_id} by {changed_by}."
        audit_entry = {
            "audit_id": audit_id,
            "claim_id": claim_id,
            "changed_by": changed_by,
            "change_timestamp": change_timestamp,
            "change_description": desc
        }
        self.claim_audits[audit_id] = audit_entry

        return {"success": True, "message": f"Claim successfully assigned to agent {agent_id}."}


    def log_claim_audit_entry(
        self,
        claim_id: str,
        changed_by: str,
        change_timestamp: str,
        change_description: str
    ) -> dict:
        """
        Record an audit entry describing a change/action performed on a claim.

        Args:
            claim_id (str): The unique ID of the claim being audited.
            changed_by (str): The ID (agent, staff, or customer) who performed the change.
            change_timestamp (str): When the change happened (ISO datetime string).
            change_description (str): Description of the action/change.

        Returns:
            dict: {
                "success": True,
                "message": "Audit entry recorded."
            }
            or
            {
                "success": False,
                "error": str  # Explanation of why it failed
            }

        Constraints:
            - claim_id must exist.
            - audit_id must be unique (generated here).
            - All required fields must be supplied and non-empty.
        """
        if not claim_id:
            return { "success": False, "error": "Missing claim_id." }
        if not changed_by:
            return { "success": False, "error": "Missing changed_by." }
        if not change_timestamp:
            return { "success": False, "error": "Missing change_timestamp." }
        if not change_description:
            return { "success": False, "error": "Missing change_description." }
        if claim_id not in self.claims:
            return { "success": False, "error": f"Claim ID '{claim_id}' does not exist." }

        # Auto-generate a unique audit_id
        audit_id = str(uuid.uuid4())
        while audit_id in self.claim_audits:
            audit_id = str(uuid.uuid4())

        new_entry = {
            "audit_id": audit_id,
            "claim_id": claim_id,
            "changed_by": changed_by,
            "change_timestamp": change_timestamp,
            "change_description": change_description
        }

        self.claim_audits[audit_id] = new_entry
        return { "success": True, "message": "Audit entry recorded." }

    def create_claim(
        self,
        claim_id: str,
        customer_id: str,
        details: str,
        submission_date: str,
        assigned_agent_id: str = ""
    ) -> dict:
        """
        Submit a new insurance claim with provided customer and initial details.

        Args:
            claim_id (str): Unique identifier for the claim.
            customer_id (str): Customer who submits the claim (must exist).
            details (str): Initial claim details and description.
            submission_date (str): Submission timestamp in ISO format.
            assigned_agent_id (str, optional): Initial agent assignment; may be empty or must be valid if given.

        Returns:
            dict:
                - On success: { "success": True, "message": "Claim <claim_id> created successfully." }
                - On error: { "success": False, "error": "<reason>" }

        Constraints:
            - claim_id must be unique (not already in self.claims).
            - customer_id must exist in self.customers.
            - If assigned_agent_id is provided (not ""), it must exist in self.agents.
            - Status should initially be "submitted".
            - Claim creation must be logged in ClaimAudit.
        """
        # Check unique claim_id
        if claim_id in self.claims:
            return { "success": False, "error": "Claim ID already exists." }
        # Check customer exists
        if customer_id not in self.customers:
            return { "success": False, "error": "Customer does not exist." }
        # Check agent (if given)
        if assigned_agent_id and assigned_agent_id not in self.agents:
            return { "success": False, "error": "Assigned agent does not exist." }
        # Minimal detail check (optional — can be omitted if not needed)
        if not details or details.strip() == "":
            return { "success": False, "error": "Claim details cannot be empty." }
        # Create initial claim record
        self.claims[claim_id] = {
            "claim_id": claim_id,
            "customer_id": customer_id,
            "status": "submitted",
            "submission_date": submission_date,
            "details": details,
            "assigned_agent_id": assigned_agent_id
        }
        # Log the creation in ClaimAudit
        audit_id = str(uuid.uuid4())
        claim_audit = {
            "audit_id": audit_id,
            "claim_id": claim_id,
            "changed_by": customer_id,
            "change_timestamp": submission_date if submission_date else str(time.time()),
            "change_description": "Claim created"
        }
        self.claim_audits[audit_id] = claim_audit
        return { "success": True, "message": f"Claim {claim_id} created successfully." }

    def update_claim_details(
        self, 
        claim_id: str, 
        new_details: str, 
        changed_by: str
    ) -> dict:
        """
        Edit the 'details' contents of an existing claim and log the change for auditing.

        Args:
            claim_id (str): Unique identifier of the claim to update.
            new_details (str): The updated details/content for the claim.
            changed_by (str): ID of agent or customer making the change (for audit).

        Returns:
            dict: 
              Success: 
                {"success": True, "message": "Claim details updated"}
              Failure: 
                {"success": False, "error": <reason>}
    
        Constraints:
            - The claim_id must exist.
            - All changes must be logged in ClaimAudit (with audit_id, claim_id, changed_by, timestamp, description).
        """

        # Check if claim exists
        if claim_id not in self.claims:
            return { "success": False, "error": "Claim not found" }

        # Update the claim's details
        self.claims[claim_id]["details"] = new_details

        # Create audit trail entry
        audit_id = str(uuid.uuid4())
        claim_audit_entry = {
            "audit_id": audit_id,
            "claim_id": claim_id,
            "changed_by": changed_by,
            "change_timestamp": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),  # Human-readable timestamp
            "change_description": "Details updated"
        }
        self.claim_audits[audit_id] = claim_audit_entry

        return { "success": True, "message": "Claim details updated" }

    def delete_claim(self, claim_id: str, admin_agent_id: str) -> dict:
        """
        Permanently delete a claim. Only agents with the 'admin' role can perform this action.

        Args:
            claim_id (str): The unique claim identifier to delete.
            admin_agent_id (str): The agent requesting deletion (must have admin role).

        Returns:
            dict:
                - On success:
                    { "success": True, "message": "Claim <claim_id> deleted permanently." }
                - On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure: not found, not admin, etc.
                    }

        Constraints:
            - Only agents with 'admin' role may delete claims.
            - All deletion actions must be logged in ClaimAudit.
            - If claim does not exist, deletion fails.
            - Audit trail itself is not deleted.
        """

        # Check agent exists
        agent = self.agents.get(admin_agent_id)
        if not agent:
            return { "success": False, "error": "Agent does not exist." }

        # Check agent role is admin
        if agent.get("role") != "admin":
            return { "success": False, "error": "Only admin agents can delete claims." }

        # Check claim exists
        claim = self.claims.get(claim_id)
        if not claim:
            return { "success": False, "error": "Claim does not exist." }

        # Remove claim from self.claims
        del self.claims[claim_id]

        # Log deletion in ClaimAudit
        audit_id = f"delete-{claim_id}-{int(time.time()*1000)}"
        change_description = f"Claim {claim_id} permanently deleted by admin {admin_agent_id}."
        audit_entry = {
            "audit_id": audit_id,
            "claim_id": claim_id,
            "changed_by": admin_agent_id,
            "change_timestamp": str(int(time.time())),
            "change_description": change_description,
        }
        self.claim_audits[audit_id] = audit_entry

        return { "success": True, "message": f"Claim {claim_id} deleted permanently." }


    def correct_claim_customer(self, claim_id: str, new_customer_id: str, actor_id: str) -> dict:
        """
        Re-link a claim to a different customer in case of error.

        Args:
            claim_id (str): Claim to be re-linked.
            new_customer_id (str): Customer to link to.
            actor_id (str): User/agent performing the change.

        Returns:
            dict: {
                "success": True,
                "message": "Claim <claim_id> successfully re-linked to customer <new_customer_id>."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - Both claim_id and new_customer_id must exist.
            - Action must be logged in ClaimAuditInfo.
        """
        # Validate claim existence
        if claim_id not in self.claims:
            return { "success": False, "error": f"Claim ID '{claim_id}' does not exist." }
    
        # Validate new customer existence
        if new_customer_id not in self.customers:
            return { "success": False, "error": f"Customer ID '{new_customer_id}' does not exist." }
    
        # Validate actor existence
        if actor_id not in self.agents and actor_id not in self.customers:
            return { "success": False, "error": f"Actor ID '{actor_id}' does not exist." }
    
        # Check if change is necessary
        old_customer_id = self.claims[claim_id]['customer_id']
        if old_customer_id == new_customer_id:
            return { "success": False, "error": "Claim already linked to the specified customer." }
    
        # Perform re-link
        self.claims[claim_id]['customer_id'] = new_customer_id

        # Audit logging
        change_description = (
            f"Changed claim '{claim_id}' customer from '{old_customer_id}' to '{new_customer_id}' by actor '{actor_id}'."
        )
        audit_id = str(uuid.uuid4())
        change_timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

        audit_entry = {
            "audit_id": audit_id,
            "claim_id": claim_id,
            "changed_by": actor_id,
            "change_timestamp": change_timestamp,
            "change_description": change_description
        }
        self.claim_audits[audit_id] = audit_entry

        return { 
            "success": True, 
            "message": f"Claim '{claim_id}' successfully re-linked to customer '{new_customer_id}'."
        }

    def restore_deleted_claim(self, claim_id: str) -> dict:
        """
        Recover a previously deleted insurance claim from audit logs, if possible.

        Args:
            claim_id (str): The unique claim identifier to restore.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Claim <claim_id> was restored successfully."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "reason for restoration failure"
                    }

        Constraints:
            - Can only restore claims that were deleted (not present in self.claims).
            - Restoration is allowed only if all necessary claim data is available in the audit trail.
            - Must log restoration as a new ClaimAudit entry.
            - Must ensure claim_id uniqueness.

        Notes:
            - If audit log does not contain enough info to reconstruct the claim, restoration fails.
        """

        # If claim_id is already in claims, nothing to restore
        if claim_id in self.claims:
            return {
                "success": False,
                "error": f"Claim '{claim_id}' already exists and is not deleted."
            }

        # Scan audit log for "delete" and previous claim data
        # Try to reconstruct the claim info from the most recent pre-delete entry
        restore_data = None
        latest_pre_delete = None
        delete_audit_timestamp = None

        # Find the audit entries for this claim_id, in order
        audits = [
            a for a in self.claim_audits.values()
            if a["claim_id"] == claim_id
        ]
        # Sort audits by change_timestamp ascending
        audits.sort(key=lambda a: a["change_timestamp"])

        # Find last audit entry BEFORE deletion
        for audit in audits:
            if "delete" in audit["change_description"].lower():
                delete_audit_timestamp = audit["change_timestamp"]
                break
            latest_pre_delete = audit

        if not delete_audit_timestamp:
            return {
                "success": False,
                "error": f"No record found of claim '{claim_id}' being deleted."
            }
        # Attempt to reconstruct prior claim info from latest_pre_delete
        if not latest_pre_delete or "claim data:" not in latest_pre_delete["change_description"].lower():
            return {
                "success": False,
                "error": f"Could not find sufficient data to restore claim '{claim_id}'."
            }

        # Assume previous audit logged full claim info after "claim data:" in change_description
        try:
            # Expecting claim data in the form "claim data: {...}"
            desc = latest_pre_delete["change_description"]
            if "claim data:" in desc.lower():
                # Extract the substring after "claim data:"
                prefix_idx = desc.lower().index("claim data:") + len("claim data:")
                claim_data_str = desc[prefix_idx:].strip()
                # Try to parse claim_data_str as dict
                restored_claim = ast.literal_eval(claim_data_str)
                # Safety checks
                if not isinstance(restored_claim, dict):
                    raise Exception("Data format error")
            else:
                return {
                    "success": False,
                    "error": f"Audit entry does not contain claim data for '{claim_id}'."
                }
        except Exception:
            return {
                "success": False,
                "error": f"Could not parse audit claim data for '{claim_id}'."
            }

        # Add the restored claim back to self.claims
        self.claims[claim_id] = restored_claim

        # Log restoration in audit trail
        now_timestamp = str(time.time())
        restore_audit = {
            "audit_id": str(uuid.uuid4()),
            "claim_id": claim_id,
            "changed_by": "system_restore",
            "change_timestamp": now_timestamp,
            "change_description": "Claim restored from deletion using audit log."
        }
        self.claim_audits[restore_audit["audit_id"]] = restore_audit

        return {
            "success": True,
            "message": f"Claim '{claim_id}' was restored successfully."
        }
