import frappe
from frappe.utils import flt, cint
import random
from collections import defaultdict


class IntelligentRollPicker:
    """
    Intelligent roll picker for AQL-based fabric inspection sampling
    Prioritizes diversity-based sampling for representative quality assessment
    """

    def __init__(self, inspection_doc):
        self.inspection_doc = inspection_doc
        self.total_rolls = len(inspection_doc.fabric_rolls_tab or [])
        self.required_sample_rolls = cint(inspection_doc.required_sample_rolls or 1)

    def auto_pick_rolls(self):
        """
        Automatically pick rolls for inspection based on inspection type
        Returns list of roll names that should be marked as autopicked

        Supports:
        - AQL Based: Uses intelligent diversity-based sampling
        - 100% Inspection: Picks ALL rolls
        - Custom Sampling: Picks based on sampling percentage or required sample count
        """
        if not self.inspection_doc.fabric_rolls_tab:
            return []

        inspection_type = self.inspection_doc.inspection_type

        if inspection_type == 'AQL Based':
            # Existing AQL logic with intelligent sampling
            if self.required_sample_rolls >= self.total_rolls:
                selected_rolls = [roll.name for roll in self.inspection_doc.fabric_rolls_tab]
            else:
                selected_rolls = self._diversity_based_selection()

        elif inspection_type == '100% Inspection':
            # Pick ALL rolls for 100% inspection
            selected_rolls = [roll.name for roll in self.inspection_doc.fabric_rolls_tab]

        elif inspection_type == 'Custom Sampling':
            # Pick based on custom sampling configuration
            selected_rolls = self._custom_sampling_selection()

        else:
            # Fallback for any other inspection type
            selected_rolls = []

        # Log the autopicking decision
        frappe.logger().info(f"Auto-picked {len(selected_rolls)} rolls out of {self.total_rolls} "
                           f"for {inspection_type} inspection {self.inspection_doc.name}")

        return selected_rolls

    def _diversity_based_selection(self):
        """
        Select rolls using diversity-based stratified sampling approach
        Ensures representative sampling across different roll characteristics
        """
        rolls = list(self.inspection_doc.fabric_rolls_tab)

        if len(rolls) <= self.required_sample_rolls:
            return [roll.name for roll in rolls]

        # Step 1: Group rolls by key characteristics for stratified sampling
        strata = self._create_strata(rolls)

        # Step 2: Calculate samples per stratum
        selected_rolls = []
        remaining_samples = self.required_sample_rolls

        # Proportional allocation with minimum 1 per stratum if possible
        for stratum_key, stratum_rolls in strata.items():
            if remaining_samples <= 0:
                break

            stratum_size = len(stratum_rolls)
            # Calculate proportional sample size
            proportion = stratum_size / self.total_rolls
            stratum_samples = max(1, min(remaining_samples,
                                       round(self.required_sample_rolls * proportion)))

            # Randomly select from this stratum
            if stratum_samples >= stratum_size:
                # Take all from this stratum
                selected_rolls.extend([roll.name for roll in stratum_rolls])
                remaining_samples -= stratum_size
            else:
                # Random sample from stratum
                sampled = random.sample(stratum_rolls, stratum_samples)
                selected_rolls.extend([roll.name for roll in sampled])
                remaining_samples -= stratum_samples

        # Step 3: If we still need more samples, randomly pick from remaining
        if len(selected_rolls) < self.required_sample_rolls:
            remaining_rolls = [roll for roll in rolls if roll.name not in selected_rolls]
            additional_needed = self.required_sample_rolls - len(selected_rolls)

            if remaining_rolls and additional_needed > 0:
                additional = random.sample(remaining_rolls,
                                         min(additional_needed, len(remaining_rolls)))
                selected_rolls.extend([roll.name for roll in additional])

        return selected_rolls[:self.required_sample_rolls]

    def _custom_sampling_selection(self):
        """
        Select rolls for custom sampling based on sampling percentage or sample count
        Uses intelligent sampling for representative quality assessment
        """
        rolls = list(self.inspection_doc.fabric_rolls_tab)

        # If no rolls, return empty
        if not rolls:
            return []

        # Check if we have a sampling percentage defined
        sampling_percentage = flt(getattr(self.inspection_doc, 'sampling_percentage', 0))

        # Calculate required samples based on percentage or use required_sample_rolls
        if sampling_percentage > 0:
            # Calculate based on percentage
            calculated_samples = max(1, round((sampling_percentage / 100) * self.total_rolls))
            required_samples = min(calculated_samples, self.total_rolls)
        else:
            # Use required_sample_rolls field
            required_samples = min(self.required_sample_rolls, self.total_rolls)

        # If sample count >= total rolls, pick all
        if required_samples >= self.total_rolls:
            return [roll.name for roll in rolls]

        # Use diversity-based selection for representative sampling
        # Temporarily update required_sample_rolls for the selection logic
        original_required = self.required_sample_rolls
        self.required_sample_rolls = required_samples

        selected_rolls = self._diversity_based_selection()

        # Restore original value
        self.required_sample_rolls = original_required

        return selected_rolls

    def _create_strata(self, rolls):
        """
        Create strata (groups) of rolls based on key characteristics
        Prioritizes diversity in: shade, GSM range, length range
        """
        strata = defaultdict(list)

        for roll in rolls:
            # Create stratum key based on multiple characteristics
            stratum_key = self._get_stratum_key(roll)
            strata[stratum_key].append(roll)

        # If too few strata, create broader groupings
        if len(strata) < 2 and len(rolls) > 2:
            # Fall back to length-based strata
            return self._create_length_based_strata(rolls)

        return dict(strata)

    def _get_stratum_key(self, roll):
        """
        Generate stratum key for a roll based on its characteristics
        Combines shade, GSM range, and length range
        """
        # Shade grouping
        shade = getattr(roll, 'shade_code', '') or getattr(roll, 'inspected_shade', '') or 'unknown'

        # GSM range grouping (group by 10s)
        gsm = flt(getattr(roll, 'gsm', 0))
        gsm_range = f"{int(gsm // 10) * 10}-{int(gsm // 10) * 10 + 9}" if gsm > 0 else 'unknown'

        # Length range grouping (group by 10m intervals)
        length = flt(getattr(roll, 'roll_length', 0))
        length_range = f"{int(length // 10) * 10}-{int(length // 10) * 10 + 9}" if length > 0 else 'unknown'

        return f"{shade}_{gsm_range}_{length_range}"

    def _create_length_based_strata(self, rolls):
        """
        Fallback stratification based on roll length ranges
        """
        strata = defaultdict(list)

        for roll in rolls:
            length = flt(getattr(roll, 'roll_length', 0))
            if length <= 0:
                stratum_key = 'unknown'
            elif length < 50:
                stratum_key = 'short'
            elif length < 100:
                stratum_key = 'medium'
            else:
                stratum_key = 'long'

            strata[stratum_key].append(roll)

        return dict(strata)


@frappe.whitelist()
def auto_pick_rolls_for_inspection(inspection_id):
    """
    API method to manually trigger auto-picking for an inspection
    """
    try:
        inspection = frappe.get_doc("Fabric Inspection", inspection_id)

        if not inspection.has_permission("write"):
            frappe.throw("You do not have permission to modify this inspection")

        picker = IntelligentRollPicker(inspection)
        selected_roll_names = picker.auto_pick_rolls()

        # Update the rolls
        updated_count = 0
        for roll in inspection.fabric_rolls_tab:
            if roll.name in selected_roll_names:
                roll.autopicked = 1
                updated_count += 1
            else:
                roll.autopicked = 0

        inspection.save()

        return {
            "success": True,
            "message": f"Auto-picked {updated_count} rolls for inspection",
            "data": {
                "total_rolls": len(inspection.fabric_rolls_tab),
                "autopicked_rolls": updated_count,
                "selected_roll_ids": selected_roll_names
            }
        }

    except Exception as e:
        frappe.log_error(f"Error auto-picking rolls: {str(e)}")
        return {
            "success": False,
            "message": f"Error auto-picking rolls: {str(e)}"
        }


def trigger_autopick_on_inspection_change(inspection_doc):
    """
    Trigger auto-picking when inspection configuration changes
    Works for AQL Based, 100% Inspection, and Custom Sampling
    Called from Fabric Inspection validate method
    """
    # Check if inspection type supports auto-picking
    supported_types = ['AQL Based', '100% Inspection', 'Custom Sampling']

    if inspection_doc.inspection_type in supported_types:
        picker = IntelligentRollPicker(inspection_doc)
        selected_roll_names = picker.auto_pick_rolls()

        # Clear existing autopicked flags
        for roll in inspection_doc.fabric_rolls_tab:
            roll.autopicked = 0

        # Set new autopicked flags
        for roll in inspection_doc.fabric_rolls_tab:
            if roll.name in selected_roll_names:
                roll.autopicked = 1

        frappe.logger().info(f"Auto-picked {len(selected_roll_names)} rolls "
                           f"for {inspection_doc.inspection_type} inspection {inspection_doc.name}")

# Backward compatibility - keep old function name as alias
def trigger_autopick_on_aql_change(inspection_doc):
    """
    Backward compatibility function - redirects to new function
    """
    return trigger_autopick_on_inspection_change(inspection_doc)