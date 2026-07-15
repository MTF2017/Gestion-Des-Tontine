from odoo import models, fields, api


class TontineCash(models.Model):
    _name = "tontine.cash"
    _description = "Mouvement de caisse"
    _rec_name = "name"

    name = fields.Char(
        string="Référence",
        compute="_compute_name",
        store=True
    )
    group_id = fields.Many2one(
        "tontine.group",
        string="Tontine",
        required=True
    )
    member_id = fields.Many2one(
        "tontine.member",
        string="Membre concerné"
    )
    available_member_ids = fields.Many2many(
        "tontine.member",
        compute="_compute_available_member_ids",
        string="Membres disponibles"
    )
    date = fields.Date(string="Date", default=fields.Date.today)
    move_type = fields.Selection(
        [
            ('in', 'Entrée'),
            ('out', 'Sortie')
        ],
        string="Type de mouvement",
        required=True
    )
    source = fields.Selection(
        [
            ('contribution', 'Cotisation'),
            ('penalty', 'Pénalité'),
            ('other_income', 'Autre recette'),
            ('distribution', 'Distribution'),
            ('admin_fee', 'Frais administratifs'),
            ('other_expense', 'Autre dépense')
        ],
        string="Origine"
    )
    payment_id = fields.Many2one("tontine.payment", string="Cotisation liée")
    penalty_id = fields.Many2one("tontine.penalty", string="Pénalité liée")
    distribution_id = fields.Many2one("tontine.distribution", string="Distribution liée")
    amount = fields.Float(string="Montant")
    description = fields.Char(string="Description")

    @api.depends("group_id")
    def _compute_available_member_ids(self):
        for move in self:
            if move.group_id:
                subscriptions = self.env["tontine.subscription"].search([
                    ("group_id", "=", move.group_id.id)
                ])
                move.available_member_ids = subscriptions.mapped("member_id")
            else:
                move.available_member_ids = False

    @api.onchange("group_id", "source")
    def _onchange_group_source(self):
        if self.group_id and self.member_id and self.member_id.id not in self.available_member_ids.ids:
            self.member_id = False

        if self.group_id and self.source in ("contribution", "distribution"):
            nb_members = len(self.group_id.member_ids)
            self.amount = self.group_id.amount * nb_members

        if self.source == "contribution":
            self.move_type = "in"
        elif self.source == "distribution":
            self.move_type = "out"

        return {"domain": {"member_id": [("id", "in", self.available_member_ids.ids)]}}

    @api.depends("move_type", "amount", "date", "member_id")
    def _compute_name(self):
        for move in self:
            type_label = "Entrée" if move.move_type == "in" else "Sortie" if move.move_type == "out" else ""
            member_name = move.member_id.name or ""
            date_str = move.date.strftime("%d/%m/%Y") if move.date else ""
            if type_label and member_name:
                move.name = f"{type_label} {move.amount:.0f} - {member_name} - {date_str}"
            elif type_label:
                move.name = f"{type_label} {move.amount:.0f} - {date_str}"
            else:
                move.name = "Nouveau mouvement"