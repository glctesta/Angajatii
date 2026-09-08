"""
Document Generator Service.
Generates hiring-related documents from Word templates using docxtpl.

Templates use guillemet placeholders: «placeholder»
docxtpl uses Jinja2 syntax: {{ placeholder }}

We handle both formats: the service replaces guillemets before rendering.
"""
import os
import re
from datetime import datetime, date
from typing import Optional
from docxtpl import DocxTemplate

from app.models.settings import AppSetting


class DocumentGenerator:
    """Generates Word documents from templates for the hiring process."""

    # Mapping template files -> method names
    TEMPLATES = {
        'cerere_angajare': 'CERERE_DE_ANGAJARE.docx',
        'contract': 'CONTRACT_INDIVIDUAL_DE_MUNCA.docx',
        'informare': 'CONTRACT_INDIVIDUAL_DE_MUNCA_INFORMARE.docx',
        'declaratie': 'DeclaratieAngajare.docx',
        'instiintare': 'INSTIINZAREmodel.docx',
        'predare_cartela': 'PredarePrimireCartela.docx',
        'notifica_medicina': 'NotificaServizioMedicinaDelLavoro.docx',
    }

    def __init__(self):
        self.template_path = AppSetting.get_value('DOCUMENT_TEMPLATE_PATH', r'L:\\')
        self.output_path = AppSetting.get_value('DOCUMENT_OUTPUT_PATH', r'L:\\Employees\\Documenti\\')

    def _get_template_path(self, template_key: str) -> str:
        """Get full path to template file."""
        filename = self.TEMPLATES.get(template_key)
        if not filename:
            raise ValueError(f"Template sconosciuto: {template_key}")
        path = os.path.join(self.template_path, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Template non trovato: {path}")
        return path

    def _get_output_dir(self, employee_id: int) -> str:
        """Get output directory for generated documents, create if needed."""
        year = datetime.now().strftime('%Y')
        out_dir = os.path.join(self.output_path, year, str(employee_id))
        os.makedirs(out_dir, exist_ok=True)
        return out_dir

    def _convert_guillemets(self, doc: DocxTemplate) -> None:
        """Convert «placeholder» guillemets to {{ placeholder }} Jinja2 syntax.
        This is done in-place on the docx XML before rendering.
        """
        # Access the underlying XML document
        for paragraph in doc.docx.paragraphs:
            if '«' in paragraph.text or '\xab' in paragraph.text:
                for run in paragraph.runs:
                    if '«' in run.text or '\xab' in run.text:
                        # Replace guillemets with Jinja2 syntax
                        run.text = re.sub(r'[«\xab](\w+)[»\xbb]', r'{{ \1 }}', run.text)

        # Also process tables
        for table in doc.docx.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        if '«' in paragraph.text or '\xab' in paragraph.text:
                            for run in paragraph.runs:
                                if '«' in run.text or '\xab' in run.text:
                                    run.text = re.sub(r'[«\xab](\w+)[»\xbb]', r'{{ \1 }}', run.text)

    def _render_document(self, template_key: str, context: dict, output_filename: str, employee_id: int) -> str:
        """Load template, replace placeholders, save to output directory.
        Returns the path to the generated file.
        """
        template_path = self._get_template_path(template_key)
        output_dir = self._get_output_dir(employee_id)
        output_file = os.path.join(output_dir, output_filename)

        doc = DocxTemplate(template_path)
        self._convert_guillemets(doc)
        doc.render(context)
        doc.save(output_file)

        return output_file

    def _build_common_context(self, hiring_data: dict) -> dict:
        """Build the common context dictionary for all documents."""
        ctx = {}

        # Employee personal data
        ctx['EmployeeName'] = hiring_data.get('employee_name', '')
        ctx['EmployeeSurname'] = hiring_data.get('employee_surname', '')
        ctx['CNP'] = hiring_data.get('cnp', '')
        ctx['NumeSiPrenumeSalariat'] = f"{hiring_data.get('employee_surname', '')} {hiring_data.get('employee_name', '')}"

        # Sex-dependent articles (Romanian)
        sex = hiring_data.get('sex', 'M')
        ctx['Salariato'] = 'Salariatul' if sex == 'M' else 'Salariata'
        ctx['Saluto'] = 'Dl.' if sex == 'M' else 'Dna.'
        ctx['Titolo'] = 'Dl.' if sex == 'M' else 'Dna.'
        ctx['ArticoloMF'] = 'a' if sex == 'M' else 'a'
        ctx['articoloMF'] = 'a' if sex == 'M' else 'a'
        ctx['Domicilio'] = 'domiciliat' if sex == 'M' else 'domiciliata'

        # Address
        ctx['TownName'] = hiring_data.get('town_name', '')
        ctx['Street'] = hiring_data.get('street', '')
        ctx['NumeroCivico'] = hiring_data.get('numero_civico', '')
        ctx['Bloc'] = hiring_data.get('bloc', '')
        ctx['Piano'] = hiring_data.get('piano', '')
        ctx['Apartment'] = hiring_data.get('apartment', '')
        ctx['CountyName'] = hiring_data.get('county_name', '')
        ctx['Adresa'] = hiring_data.get('full_address', '')
        ctx['AdresaSalariat'] = hiring_data.get('full_address', '')

        # Document
        ctx['DocNameRO'] = hiring_data.get('doc_type_name', 'C.I.')
        ctx['DocSerie'] = hiring_data.get('doc_serie', '')
        ctx['DocNumber'] = hiring_data.get('doc_number', '')

        # Contract
        ctx['ContractTypeRom'] = hiring_data.get('contract_type_rom', 'nedeterminata')
        ctx['TestPeriod'] = str(hiring_data.get('test_period', 90))
        ctx['IussedDateDoc'] = hiring_data.get('start_work_date_str', '')
        ctx['DataInceperiiActivitatii'] = hiring_data.get('start_work_date_str', '')
        ctx['EndWorkDateContract'] = hiring_data.get('end_work_date_str', '')
        ctx['InformDate'] = hiring_data.get('hire_date_str', '')

        # Function / COR
        ctx['CodeDescription'] = hiring_data.get('function_description', '')
        ctx['CoreHiringCode'] = hiring_data.get('core_code', '')
        ctx['CODCOR'] = hiring_data.get('core_code', '')

        # Company data
        ctx['NumeSocietate'] = hiring_data.get('company_name', '')
        ctx['Societa'] = hiring_data.get('company_name', '')
        ctx['SocInd1'] = hiring_data.get('company_address', '')
        ctx['AdresaSocietate'] = hiring_data.get('company_address', '')
        ctx['SocCitta'] = hiring_data.get('company_city', '')
        ctx['SocTel'] = hiring_data.get('company_phone', '')
        ctx['CUI'] = hiring_data.get('company_fiscal_code', '')
        ctx['CodFiscal'] = hiring_data.get('company_fiscal_code', '')
        ctx['NRC'] = hiring_data.get('company_reg_code', '')
        ctx['NrRegCom'] = hiring_data.get('company_reg_code', '')

        # Registry
        ctx['NumeroRegistro'] = hiring_data.get('contract_number', '')
        ctx['NumeroPv'] = hiring_data.get('contract_number', '')

        return ctx

    def generate_cerere_angajare(self, hiring_data: dict) -> str:
        """Generate hiring request document."""
        ctx = self._build_common_context(hiring_data)
        filename = f"CERERE_ANGAJARE_{hiring_data.get('cnp', 'N')}.docx"
        return self._render_document('cerere_angajare', ctx, filename, hiring_data['employee_id'])

    def generate_contract(self, hiring_data: dict) -> str:
        """Generate employment contract."""
        ctx = self._build_common_context(hiring_data)
        filename = f"CONTRACT_{hiring_data.get('cnp', 'N')}.docx"
        return self._render_document('contract', ctx, filename, hiring_data['employee_id'])

    def generate_informare(self, hiring_data: dict) -> str:
        """Generate contract information document."""
        ctx = self._build_common_context(hiring_data)
        filename = f"INFORMARE_{hiring_data.get('cnp', 'N')}.docx"
        return self._render_document('informare', ctx, filename, hiring_data['employee_id'])

    def generate_declaratie(self, hiring_data: dict) -> str:
        """Generate hiring declaration."""
        ctx = self._build_common_context(hiring_data)
        filename = f"DECLARATIE_{hiring_data.get('cnp', 'N')}.docx"
        return self._render_document('declaratie', ctx, filename, hiring_data['employee_id'])

    def generate_instiintare(self, hiring_data: dict) -> str:
        """Generate labor office notification."""
        ctx = self._build_common_context(hiring_data)
        filename = f"INSTIINTARE_{hiring_data.get('cnp', 'N')}.docx"
        return self._render_document('instiintare', ctx, filename, hiring_data['employee_id'])

    def generate_predare_cartela(self, hiring_data: dict) -> str:
        """Generate badge/key handover document."""
        ctx = self._build_common_context(hiring_data)
        filename = f"PREDARE_CARTELA_{hiring_data.get('cnp', 'N')}.docx"
        return self._render_document('predare_cartela', ctx, filename, hiring_data['employee_id'])

    def generate_notifica_medicina(self, hiring_data: dict) -> str:
        """Generate occupational medicine notification."""
        ctx = self._build_common_context(hiring_data)
        ctx['MedicinaMunci'] = hiring_data.get('medical_center_name', '')
        ctx['Nome'] = f"{hiring_data.get('employee_surname', '')} {hiring_data.get('employee_name', '')}"
        ctx['IndirizzoSocieta'] = hiring_data.get('company_address', '')
        filename = f"NOTIFICA_MEDICINA_{hiring_data.get('cnp', 'N')}.docx"
        return self._render_document('notifica_medicina', ctx, filename, hiring_data['employee_id'])

    def generate_all(self, hiring_data: dict) -> list:
        """Generate all documents for a hiring. Returns list of generated file paths."""
        generated = []
        methods = [
            self.generate_cerere_angajare,
            self.generate_contract,
            self.generate_informare,
            self.generate_declaratie,
            self.generate_instiintare,
            self.generate_predare_cartela,
        ]

        for method in methods:
            try:
                path = method(hiring_data)
                generated.append({'name': os.path.basename(path), 'path': path, 'success': True})
            except Exception as e:
                generated.append({'name': method.__name__, 'path': '', 'success': False, 'error': str(e)})

        # Medical notification only if medical center specified
        if hiring_data.get('medical_center_name'):
            try:
                path = self.generate_notifica_medicina(hiring_data)
                generated.append({'name': os.path.basename(path), 'path': path, 'success': True})
            except Exception as e:
                generated.append({'name': 'notifica_medicina', 'path': '', 'success': False, 'error': str(e)})

        return generated
