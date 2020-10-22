# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class StockInventory(models.Model):
    _name = 'stock.inventory'
    _inherit = ['stock.inventory', 'portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']

    check_activity_sent = fields.Boolean(string='Check Activity Sent', default=False)

    def action_open_inventory_lines(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'views': [(self.env.ref('stock.stock_inventory_line_tree2').id, 'tree')],
            'view_mode': 'tree',
            'name': _('Inventory Lines'),
            'res_model': 'stock.inventory.line',
        }
        context = {
            'default_is_editable': True,
            'default_inventory_id': self.id,
            'default_company_id': self.company_id.id,
        }
        # Define domains and context
        domain = [
            ('is_editable', '=', True),
            ('inventory_id', '=', self.id),
            ('location_id.usage', 'in', ['internal', 'transit'])
        ]
        if self.location_ids:
            context['default_location_id'] = self.location_ids[0].id
            if len(self.location_ids) == 1:
                if not self.location_ids[0].child_ids:
                    context['readonly_location_id'] = True

        if self.product_ids:
            if len(self.product_ids) == 1:
                context['default_product_id'] = self.product_ids[0].id

        action['context'] = context
        action['domain'] = domain
        return action

    @api.model
    def cron_activity_stock_inventory(self):
        lines = self.search([('state', '=', 'confirm')])
        users = self.env['res.users'].search([])
        for rec in lines:
            for user in users:
                if not rec.check_activity_sent and user.has_group(
                        'inventory_adjustments_access_right.group_inventory_adjustments_access_right') and not user.has_group(
                    'base.group_system'):
                    rec.activity_schedule(
                        'inventory_adjustments_access_right.schdule_activity_stock_inventory_manager_id',
                        user_id=user.id,
                        summary='Inventory Adjustment' + ' ' + str(rec.name) + ' ' + 'still not validated')
                    rec.check_activity_sent = True
