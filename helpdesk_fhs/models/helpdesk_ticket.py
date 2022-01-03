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
    def message_new(self, msg_dict, custom_values=None):
        # Cambiar según el nombre de la acción "servidor de correo entrante"
        fetchmail_server = self.env['fetchmail.server'].search([('name', '=', 'soporte')])
        if fetchmail_server.exists() and self._context.get('default_fetchmail_server_id', 0) == fetchmail_server.id:
            self = self.with_context(default_user_id=False)

            email_subject = html2plaintext(msg_dict.get('subject', ''))
            email_text = html2plaintext(msg_dict.get('body', ''))
            email = re.findall(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,63})", msg_dict.get('email_from'), re.MULTILINE)
            email_matches = re.findall(r"E-mail: ([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,63})", email_text, re.MULTILINE)

            # Cambiar según nombre de usuario a asignar el ticket
            user_id = self.env['res.users'].sudo().search([('login', '=', 'ruben.rubiales@lesielle.com')], limit=1)

            duplicate = False
            partner = False
            partner_user = self.env['res.partner'].sudo().search([('email', '=', email_matches[0] if len(email_matches) > 0 else email[0])], limit=1)
            
            data = {
                'name': email_subject,
                'partner_email': email_matches[0] if len(email_matches) > 0 else email[0],
                #'description': email_text,
                'partner_id': partner_user.id,
                'user_id': user_id.id if user_id.exists() else 1
            }
            


            if data['partner_email']:
                partner = self.env['res.partner'].sudo().search([('email', '=', data['partner_email'])], limit=1)
                
                if partner.exists():
                    duplicate = True
                
            if (not partner or not partner.exists()) and len(data['partner_email']) > 0:
                partner_data = {
                    'name': email_matches[0] if len(email_matches) > 0 else email[0],
                }

                if len(data['partner_email']) > 0:
                    partner_data.update({'email': data['partner_email']})

                partner = self.env['res.partner'].sudo().create(partner_data)
                data.update({'partner_id': partner.id})



            return self.create(data)
            #return super(HelpdeskTicket, self).message_new(msg_dict, custom_values=data)

