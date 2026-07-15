from odoo import models, fields, api


class TontinePenalty(models.Model):
    _name = "tontine.penalty"
    _description = "Pénalité"
    _rec_name = "name"

    name = fields.Char(
        string="Référence",
        compute="_compute_name",
        store=True
    )
    subscription_id = fields.Many2one(
        "tontine.subscription",
        string="Adhésion",
        required=True
    )
    payment_id = fields.Many2one(
        "tontine.payment",
        string="Paiement lié"
    )
    period = fields.Date(
        string="Période concernée",
        default=fields.Date.today
    )
    amount = fields.Float(
        string="Montant"
    )
    reason = fields.Char(
        string="Motif"
    )

    @api.depends("subscription_id", "period")
    def _compute_name(self):
        for penalty in self:
            sub_name = penalty.subscription_id.name or ""
            period_str = penalty.period.strftime("%m/%Y") if penalty.period else ""
            if sub_name and period_str:
                penalty.name = f"Pénalité {sub_name} - {period_str}"
            else:
                penalty.name = sub_name or "Nouvelle pénalité"
    @api.model_create_multi
    def create(self, vals_list):
        penalties = super().create(vals_list)
        for penalty in penalties:
            existing = self.env["tontine.cash"].search([("penalty_id", "=", penalty.id)], limit=1)
            if not existing:
                self.env["tontine.cash"].create({
                    "group_id": penalty.subscription_id.group_id.id,
                    "member_id": penalty.subscription_id.member_id.id,
                    "penalty_id": penalty.id,
                    "date": penalty.period or fields.Date.today(),
                    "move_type": "in",
                    "source": "penalty",
                    "amount": penalty.amount,
                    "description": f"Pénalité - {penalty.reason or ''}",
                })
        return penalties
    def unlink(self):
        cash_moves = self.env["tontine.cash"].search([("penalty_id", "in", self.ids)])
        cash_moves.unlink()
        return super().unlink()