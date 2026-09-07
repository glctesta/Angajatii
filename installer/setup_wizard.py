import re
from app.extensions import db
from app.models.auth import User, Role

def validate_password_strength(password):
    errors = []
    if len(password) < 8:
        errors.append("Almeno 8 caratteri.")
    if not re.search(r'[A-Z]', password):
        errors.append("Almeno una lettera maiuscola.")
    if not re.search(r'[a-z]', password):
        errors.append("Almeno una lettera minuscola.")
    if not re.search(r'[0-9]', password):
        errors.append("Almeno un numero.")
    if not re.search(r'[\W_]', password):
        errors.append("Almeno un carattere speciale.")
    return errors

class SetupWizard:
    def run(self):
        """Interactive CLI setup wizard."""
        print('=== Employees Management - Setup Wizard ===')
        print()
        
        # Step 1: Check if already configured
        if self._is_already_configured():
            print('Il sistema e\' gia\' configurato.')
            if not self._confirm('Vuoi riconfigurare? (s/n): '):
                return
        
        # Step 2: Database connection test
        print('[INFO] Test connessione database...')
        self._test_db_connection()
        print('[OK] Connessione riuscita.')
        
        # Step 3: Create database and tables
        print('[INFO] Configurazione database e tabelle...')
        self._setup_database()
        
        # Step 4: Company information
        company_info = self._collect_company_info()
        print('[OK] Info azienda raccolte.')
        
        # Step 5: Create SuperUserAdmin
        self._create_super_admin()
        
        # Step 6: Choose data source
        self._choose_data_import()
        
        print('[OK] Setup completato!')

    def _is_already_configured(self):
        try:
            return db.session.query(User).filter_by(IsSuperAdmin=True).first() is not None
        except Exception:
            return False

    def _confirm(self, prompt):
        ans = input(prompt).strip().lower()
        return ans in ['s', 'si', 'y', 'yes']

    def _test_db_connection(self):
        try:
            db.session.execute(db.text('SELECT 1'))
        except Exception as e:
            print(f'[ERROR] Connessione DB fallita: {e}')
            raise

    def _setup_database(self):
        from installer.db_creator import init_db
        init_db(seed=True)

    def _create_super_admin(self):
        """Create the SuperUserAdmin account."""
        print('\n--- Creazione SuperUserAdmin ---')
        username = input('Username SuperAdmin [superadmin]: ').strip() or 'superadmin'
        email = input('Email SuperAdmin: ').strip()
        
        while True:
            password = input('Password (min 8 char, maiuscola, minuscola, cifra, speciale): ')
            errors = validate_password_strength(password)
            if errors:
                print('[ERROR] Password non valida:')
                for e in errors:
                    print(f'  - {e}')
                continue
            confirm = input('Conferma password: ')
            if password != confirm:
                print('[ERROR] Le password non corrispondono.')
                continue
            break
        
        # Check if exists
        user = db.session.query(User).filter_by(Username=username).first()
        if not user:
            user = User(Username=username, Email=email, IsSuperAdmin=True, MustChangePassword=False)
            db.session.add(user)
        else:
            user.Email = email
            user.IsSuperAdmin = True
            user.MustChangePassword = False
            
        user.set_password(password)
        
        admin_role = db.session.query(Role).filter_by(RoleName='superadmin').first()
        if admin_role and admin_role not in user.roles:
            user.roles.append(admin_role)
            
        db.session.commit()
        print(f'[OK] Utente SuperAdmin {username} creato con successo.')
    
    def _choose_data_import(self):
        """Let user choose how to populate the database."""
        print('\n--- Importazione Dati ---')
        print('Come vuoi popolare il database?')
        print('  1. Importa dal database Employee esistente (SQL Server)')
        print('  2. Importa da un altro database SQL Server')
        print('  3. Importa da file (CSV/Excel)')
        print('  4. Configura API per importazione')
        print('  5. Inserimento manuale (salta importazione)')
        
        choice = input('Scelta [1-5]: ').strip()
        if choice == '1':
            self._import_from_employee_db()
        elif choice == '2':
            print('[INFO] Da implementare: altro DB SQL Server')
        elif choice == '3':
            path = input('Inserisci il percorso del file: ')
            print(f'[INFO] Da implementare: import da {path}')
        elif choice == '4':
            print('[INFO] Da implementare: import da API')
        else:
            print('[INFO] Importazione saltata. Inserimento manuale.')
    
    def _import_from_employee_db(self):
        """Import data from the existing Employee database."""
        print('[INFO] Importazione da Employee DB avviata...')
        print('[OK] Importazione completata (Mock).')
    
    def _collect_company_info(self):
        """Collect company information."""
        print('\n--- Informazioni Azienda ---')
        name = input('Nome azienda: ').strip()
        fiscal_code = input('Codice fiscale azienda: ').strip()
        reg_code = input('Codice registro: ').strip()
        return {'name': name, 'fiscal_code': fiscal_code, 'reg_code': reg_code}
