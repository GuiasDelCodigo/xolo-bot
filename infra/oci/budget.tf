resource "oci_budget_budget" "xolo_bot" {
  compartment_id = var.tenancy_id
  amount         = var.budget_amount
  reset_period   = "MONTHLY"
  target_type    = "COMPARTMENT"
  targets        = [oci_identity_compartment.xolo_bot.id]

  display_name  = "${local.name}-budget"
  description   = "Monthly budget for compartment ${var.compartment_name}"
  freeform_tags = local.common_tags
}

resource "oci_budget_alert_rule" "xolo_bot_actual_100" {
  budget_id      = oci_budget_budget.xolo_bot.id
  display_name   = "${local.name}-budget-alert-100"
  description    = "Alert when actual spend reaches 100% of budget"
  type           = "ACTUAL"
  threshold      = 100
  threshold_type = "PERCENTAGE"
  recipients     = var.budget_alert_email
  message        = "xolo-bot: actual spend reached 100% of monthly budget (${var.budget_amount} USD). Check OCI Console."
}
