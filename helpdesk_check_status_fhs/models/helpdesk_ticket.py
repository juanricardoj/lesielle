import logging, re
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.tools import email_re, email_split, html2plaintext
from odoo.exceptions import UserError, AccessError


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    @api.model
    def message_update(self, msg, update_vals=None):
        partner_ids = [x.id for x in self.env['mail.thread']._mail_find_partner_from_emails(self._ticket_email_split(msg), records=self) if x]
        self  = self.with_context(default_user_id=False, mail_create_nosubscribe=True, mail_create_nolog=True, mail_notrack=True)
        if not update_vals:
            update_vals = {}
        if self.stage_id.id == 3:
            update_vals.update({'stage_id':1})
        if partner_ids:
            self.message_subscribe(partner_ids)
        return super(HelpdeskTicket, self).message_update(msg, update_vals=update_vals)
