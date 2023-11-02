# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from markupsafe import Markup

from odoo.tests.common import tagged, users, HttpCase


@tagged('post_install', '-at_install', 'knowledge', 'knowledge_tour')
class TestKnowledgeEditorCommands(HttpCase):
    """
    This test suit run tours to test the new editor commands of Knowledge.
    """
    @classmethod
    def setUpClass(cls):
        super(TestKnowledgeEditorCommands, cls).setUpClass()
        # remove existing articles to ease tour management
        cls.env['knowledge.article'].search([]).unlink()
        cls.article = cls.env['knowledge.article'].create({
            'name': 'EditorCommandsArticle',
            'body': Markup('<p><br></p>'),
            'sequence': 1,
        })

    def test_knowledge_article_command_tour(self):
        """Test the /article command in the editor"""
        self.start_tour('/web', 'knowledge_article_command_tour', login='admin', step_delay=100)

    def test_knowledge_article_command_dialog_tour(self):
        """Test the /article command in a dialog"""
        self.env['knowledge.article'].create({
            'name': 'LinkedArticle',
            'body': Markup('<p><br></p>'),
            'sequence': 2,
        })
        self.start_tour('/web', 'knowledge_article_command_dialog_tour', login='admin')

    def test_knowledge_file_command_tour(self):
        """Test the /file command in the editor"""
        self.start_tour('/web', 'knowledge_file_command_tour', login='admin', step_delay=100)

    def test_knowledge_index_command_tour(self):
        """Test the /index command in the editor"""
        self.start_tour('/web', 'knowledge_index_command_tour', login='admin', step_delay=100)

    def test_knowledge_kanban_command_tour(self):
        """Test the /kanban command in the editor"""
        self.start_tour('/web', 'knowledge_kanban_command_tour', login='admin', step_delay=100)
        # Test the behaviour of the kanban when the parent article is readonly
        self.article.write({
            'article_member_ids': [(0, 0, {
                'partner_id': self.ref('base.user_admin'),
                'permission': 'write',
            })],
            'internal_permission': 'read',
        })
        self.start_tour('/web', 'knowledge_readonly_item_kanban_tour', login='demo')

    def test_knowledge_list_command_tour(self):
        """Test the /list command in the editor"""
        self.start_tour('/web', 'knowledge_list_command_tour', login='admin', step_delay=100)
        # Test the behaviour of the list when the parent article is readonly
        self.article.write({
            'article_member_ids': [(0, 0, {
                'partner_id': self.ref('base.user_admin'),
                'permission': 'write',
            })],
            'internal_permission': 'read',
        })
        self.start_tour('/web', 'knowledge_readonly_item_list_tour', login='demo')

    def test_knowledge_outline_command_tour(self):
        """Test the /outline command in the editor"""
        self.start_tour('/web', 'knowledge_outline_command_tour', login='admin', step_delay=100)

    def test_knowledge_table_of_content_command_tour(self):
        """Test the /toc command in the editor"""
        self.start_tour('/web', 'knowledge_table_of_content_command_tour', login='admin', step_delay=100)

    def test_knowledge_template_command_tour(self):
        """Test the /template command in the editor"""
        partner_ids = self.env['res.partner'].create({'name': 'HelloWorldPartner', 'email': 'helloworld@part.ner'}).ids
        article = self.env['knowledge.article'].search([('name', '=', 'EditorCommandsArticle')])[0]
        article.message_subscribe(partner_ids)
        self.start_tour('/web', 'knowledge_template_command_tour', login='admin', step_delay=100)
