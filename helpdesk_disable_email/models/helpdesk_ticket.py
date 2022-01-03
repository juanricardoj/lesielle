# -*- coding: utf-8 -*-
from odoo import models, fields, api

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    send_email = fields.Boolean('Enviar email', default=False)

    @api.model
    def create(self, values):
        if 'send_email' in values and values['send_email']:
            return super(HelpdeskTicket, self).create(values)
        else:
            return super(HelpdeskTicket, self.with_context(mail_create_nosubscribe=True, mail_create_nolog=True, mail_notrack=True)).create(values)