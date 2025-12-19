from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_cors import CORS
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.security import check_password_hash
import requests
from sqlalchemy import and_, extract
import os


app = Flask(__name__)
#CORS(app)
#CORS(app, resources={r"/*": {"origins": "*"}})
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)


# Configuração do MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
   'DATABASE_URL',
   'mysql+pymysql://igreja_user:Jb141186@localhost:3306/igreja_db?charset=utf8mb4'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sua-chave-secreta-aqui')
app.config['JSON_AS_ASCII'] = False  # Para suportar caracteres UTF-8


db = SQLAlchemy(app)


# ==================== MODELS ====================
class Role(db.Model):
   __tablename__ = 'roles'
  
   id = db.Column(db.Integer, primary_key=True)
   name = db.Column(db.String(100), unique=True, nullable=False)
   is_system = db.Column(db.Boolean, default=False)
   permissions = db.Column(db.JSON)
   created_at = db.Column(db.DateTime, default=datetime.utcnow)
  
   users = db.relationship('User', backref='role', lazy=True)
  
   def to_dict(self):
       return {
           'id': self.id,
           'name': self.name,
           'isSystem': self.is_system,
           'permissions': self.permissions
       }



class EBDClass(db.Model):
   __tablename__ = 'ebd_classes'
  
   id = db.Column(db.Integer, primary_key=True)
   name = db.Column(db.String(100), nullable=False)
   slug = db.Column(db.String(100), unique=True, nullable=False)
   password = db.Column(db.String(255), nullable=False)
   created_at = db.Column(db.DateTime, default=datetime.utcnow)
  
   members = db.relationship('Member', backref='ebd_class', lazy=True)
  
   def to_dict(self):
       return {
           'id': self.id,
           'name': self.name,
           'slug': self.slug
       }


class Member(db.Model):
   __tablename__ = 'members'
  
   id = db.Column(db.Integer, primary_key=True)
   name = db.Column(db.String(200), nullable=False)
   email = db.Column(db.String(200), unique=True)
   phone = db.Column(db.String(20))
   birth_date = db.Column(db.Date)
   address = db.Column(db.Text)
   role = db.Column(db.String(100))
   ministry_time = db.Column(db.String(50))
   is_baptized = db.Column(db.Boolean, default=False)
   how_found_church = db.Column(db.String(200))
   ministry = db.Column(db.String(100))
   suggestions = db.Column(db.Text)
   status = db.Column(db.String(20), default='Ativo', nullable=False)  # Ativo, Afastado, Saiu
   ebd_class_id = db.Column(db.Integer, db.ForeignKey('ebd_classes.id'))
   created_at = db.Column(db.DateTime, default=datetime.utcnow)
   updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
   cpf = db.Column(db.String(20),  unique=True)
   sexo = db.Column(db.String(10))
   date_conversion = db.Column(db.Date)
   last_birthday_message_sent = db.Column(db.Date, nullable=True)  # Add this line

   transactions = db.relationship('Transaction', backref='member', lazy=True, cascade='all, delete-orphan')
   attendances = db.relationship('Attendance', backref='member', lazy=True, cascade='all, delete-orphan')
  
   def to_dict(self):
       return {
           'id': self.id,
           'name': self.name,
           'email': self.email,
           'phone': self.phone,
           'birthDate': self.birth_date.isoformat() if self.birth_date else None,
           'address': self.address,
           'role': self.role,
           'ministryTime': self.ministry_time,
           'isBaptized': self.is_baptized,
           'howFoundChurch': self.how_found_church,
           'ministry': self.ministry,
           'suggestions': self.suggestions,
           'status': self.status,
           'ebdClassId': self.ebd_class_id,
           'ebdClassName': self.ebd_class.name if self.ebd_class else None,
           "cpf": self.cpf,
            "sexo" : self.sexo,
           'conversion_date': self.date_conversion.isoformat() if self.date_conversion else None,
           'last_birthday_message': self.last_birthday_message_sent.isoformat() if self.last_birthday_message_sent else None,


       }


class Transaction(db.Model):
   __tablename__ = 'transactions'
  
   id = db.Column(db.Integer, primary_key=True)
   type = db.Column(db.String(20), nullable=False)
   category = db.Column(db.String(100), nullable=False)
   description = db.Column(db.Text)
   amount = db.Column(db.Numeric(10, 2), nullable=False)
   date = db.Column(db.Date, nullable=False)
   member_id = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='CASCADE'))
   created_at = db.Column(db.DateTime, default=datetime.utcnow)
  
   def to_dict(self):
       return {
           'id': self.id,
           'type': self.type,
           'category': self.category,
           'description': self.description,
           'amount': float(self.amount),
           'date': self.date.isoformat(),
           'memberId': self.member_id,
           'memberName': self.member.name if self.member else None
       }


class Attendance(db.Model):
   __tablename__ = 'attendance'
  
   id = db.Column(db.Integer, primary_key=True)
   member_id = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='CASCADE'), nullable=False)
   date = db.Column(db.Date, nullable=False)
   present = db.Column(db.Boolean, default=False)
   service_type = db.Column(db.String(50))
   created_at = db.Column(db.DateTime, default=datetime.utcnow)
  
   def to_dict(self):
       return {
           'id': self.id,
           'memberId': self.member_id,
           'memberName': self.member.name if self.member else None,
           'date': self.date.isoformat(),
           'present': self.present,
           'serviceType': self.service_type
       }


class User(db.Model):
   __tablename__ = 'users'
  
   id = db.Column(db.Integer, primary_key=True)
   username = db.Column(db.String(100), unique=True, nullable=False)
   password_hash = db.Column(db.String(255), nullable=False)
   role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
   created_at = db.Column(db.DateTime, default=datetime.utcnow)



  
   def set_password(self, password):
       self.password_hash = generate_password_hash(password)
  
   def check_password(self, password):
       return check_password_hash(self.password_hash, password)
  
   def to_dict(self):
       return {
           'id': self.id,
           'username': self.username,
           'role': self.role.name if self.role else None,
           'permissions': self.role.permissions if self.role else []
       }


class Ministry(db.Model):
   __tablename__ = 'ministries'
  
   id = db.Column(db.Integer, primary_key=True)
   name = db.Column(db.String(100), unique=True, nullable=False)
   description = db.Column(db.Text)
   created_at = db.Column(db.DateTime, default=datetime.utcnow)
  
   def to_dict(self):
       return {
           'id': self.id,
           'name': self.name,
           'description': self.description
       }



# ==================== ROUTES - APP CHURCHES ====================

class Church(db.Model):
    __tablename__ = 'churches'
    
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    schedule = db.relationship('ChurchSchedule', backref='church', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'schedule': [item.to_dict() for item in self.schedule] if self.schedule else []
        }


class ChurchSchedule(db.Model):
    __tablename__ = 'church_schedules'
    
    id = db.Column(db.String(50), primary_key=True)
    church_id = db.Column(db.String(50), db.ForeignKey('churches.id', ondelete='CASCADE'), nullable=False)
    day = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    time = db.Column(db.String(10), nullable=False)  # Formato HH:MM

    def to_dict(self):
        return {
            'id': self.id,
            'day': self.day,
            'title': self.title,
            'description': self.description,
            'time': self.time
        }
# ==================== ROUTES - APP CHURCHES ====================



class AppConfig(db.Model):
    __tablename__ = 'app_config'
    
    id = db.Column(db.Integer, primary_key=True)
    weekly_schedule = db.Column(db.JSON, nullable=False)
    slides = db.Column(db.JSON, nullable=True)
    slide_interval = db.Column(db.Integer, default=5000)
    consolidation_stages = db.Column(db.JSON, nullable=False)
    welcome_message_new_convert = db.Column(db.Text, nullable=True)
    welcome_message_regular_member = db.Column(db.Text, nullable=True)
    evolution_api_url = db.Column(db.String(255), nullable=True)
    evolution_api_key = db.Column(db.String(255), nullable=True)
    evolution_instance_name = db.Column(db.String(100), nullable=True)
    birthday_message_enabled = db.Column(db.Boolean, default=False)
    birthday_message_time = db.Column(db.String(10), nullable=True)
    birthday_message_template = db.Column(db.Text, nullable=True)

    birthday_auto_send = db.Column(db.Boolean, default=True, nullable=False)
    birthday_auto_time = db.Column(db.String(10), default="14:40", nullable=True)
    # New fields for contact and social media
    contact_address = db.Column(db.String(255), nullable=True)
    contact_phone = db.Column(db.String(20), nullable=True)
    social_instagram = db.Column(db.String(100), nullable=True)
    social_facebook = db.Column(db.String(100), nullable=True)
    social_youtube = db.Column(db.String(100), nullable=True)

    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'weeklySchedule': self.weekly_schedule,
            'slides': self.slides or [],
            'slideInterval': self.slide_interval,
            'consolidationStages': self.consolidation_stages,
            'welcomeMessageNewConvert': self.welcome_message_new_convert,
            'welcomeMessageRegularMember': self.welcome_message_regular_member,
            'evolutionApiUrl': self.evolution_api_url,
            'evolutionApiKey': self.evolution_api_key,
            'evolutionInstanceName': self.evolution_instance_name,
            'birthdayAutoSend': self.birthday_auto_send,
            'birthdayAutoTime': self.birthday_auto_time,
            'birthdayMessageEnabled': self.birthday_message_enabled,
            'birthdayMessageTime': self.birthday_message_time,
            'birthdayMessageTemplate': self.birthday_message_template,
              # ... existing fields ...
            'contactAddress': self.contact_address,
            'contactPhone': self.contact_phone,
            'socialInstagram': self.social_instagram,
            'socialFacebook': self.social_facebook,
            'socialYoutube': self.social_youtube,

            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }


class AboutUs(db.Model):
    __tablename__ = 'about_us'
    id = db.Column(db.Integer, primary_key=True)
    history = db.Column(db.Text)
    mission = db.Column(db.Text)
    vision = db.Column(db.Text)
    video_url = db.Column(db.String(255))
    gallery_images = db.Column(db.JSON)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'history': self.history,
            'mission': self.mission,
            'vision': self.vision,
            'videoUrl': self.video_url,
            'galleryImages': self.gallery_images or [],
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }






# ==================== ROUTES - MEMBERS ====================


@app.route('/api/members', methods=['GET'])
def get_members():
   ministry = request.args.get('ministry')
   query = Member.query
  
   if ministry:
       query = query.filter_by(ministry=ministry)
  
   members = query.all()
   return jsonify([m.to_dict() for m in members])


@app.route('/api/members/<int:id>', methods=['GET'])
def get_member(id):
   member = Member.query.get_or_404(id)
   return jsonify(member.to_dict())


@app.route('/api/members', methods=['POST'])
def create_member():
    try:
        data = request.get_json()
        print(data)
        
        # Validate required fields
        required_fields = ['name', 'cpf']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Campo obrigatório ausente: {field}'}), 400
        
        # Check if member with same CPF already exists
        if Member.query.filter_by(cpf=data['cpf']).first():
            return jsonify({'error': 'Já existe um membro cadastrado com este CPF'}), 400
            
        # Parse birth date if provided
        birth_date = None
        if data.get('birthDate'):
            try:
                birth_date = datetime.fromisoformat(data['birthDate']).date()
            except (ValueError, TypeError):
                return jsonify({'error': 'Formato de data inválido. Use o formato AAAA-MM-DD'}), 400

        date_conversion = None
        if data.get('conversion_date'):
            try:
                date_conversion = datetime.fromisoformat(data['conversion_date']).date()
            except (ValueError, TypeError):
                return jsonify({'error': 'Formato de data inválido. Use o formato AAAA-MM-DD'}), 400

        last_birthday_message_sent = None
        if data.get('last_birthday_message'):
            try:
                last_birthday_message_sent = datetime.fromisoformat(data['last_birthday_message']).date()
            except (ValueError, TypeError):
                return jsonify({'error': 'Formato de data inválido para last_birthday_message. Use o formato AAAA-MM-DD'}), 400



        # Create member
        member = Member(
            name=data['name'].strip(),
            email=data.get('email', '').strip().lower() if data.get('email') else None,
            phone=data.get('phone', '').strip() if data.get('phone') else None,
            birth_date=birth_date,
            address=data.get('address', '').strip() if data.get('address') else None,
            role=data.get('role'),
            ministry_time=data.get('ministryTime'),
            is_baptized=bool(data.get('isBaptized', False)),
            how_found_church=data.get('howFoundChurch'),
            ministry=data.get('ministry'),
            suggestions=data.get('suggestions'),
            status=data.get('status', 'Ativo'),
            ebd_class_id=data.get('ebdClassId'),
            cpf=data['cpf'].strip(),
            sexo=data.get('sexo'),
            date_conversion=date_conversion,
            last_birthday_message_sent = last_birthday_message_sent

            
        )
        
        # Add to session and commit
        db.session.add(member)
        db.session.commit()
        
        return jsonify(member.to_dict()), 201
        
    except IntegrityError as e:
        db.session.rollback()
        error_msg = str(e.orig)
        if 'email' in error_msg:
            return jsonify({'error': 'Este e-mail já está cadastrado. Por favor, use outro e-mail.'}), 400
        elif 'cpf' in error_msg:
            return jsonify({'error': 'Este CPF já está cadastrado. Por favor, verifique os dados.'}), 400
        app.logger.error(f'Erro de integridade ao criar membro: {error_msg}')
        return jsonify({'error': 'Erro ao salvar o membro. Dados duplicados ou inválidos.'}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Erro ao criar membro: {str(e)}', exc_info=True)
        return jsonify({'error': 'Erro ao salvar o membro. Por favor, tente novamente.'}), 500


@app.route('/api/members/<int:id>', methods=['PUT'])
def update_member(id):
    try:
        app.logger.info(f'Updating member ID: {id}')
        member = Member.query.get_or_404(id)
        data = request.get_json()
        print(data)
        
        if not data:
            app.logger.error('No data provided in request')
            return jsonify({'error': 'Nenhum dado fornecido para atualização'}), 400
            
        app.logger.info(f'Update data received: {data}')
        
        # Validate required fields
        if 'name' in data and not data['name']:
            app.logger.warning('Empty name provided in update')
            return jsonify({'error': 'O nome não pode estar vazio'}), 400
            
        if 'cpf' in data and not data['cpf']:
            app.logger.warning('Empty CPF provided in update')
            return jsonify({'error': 'O CPF não pode estar vazio'}), 400
        
        # Check for duplicate CPF (if CPF is being updated)
        if 'cpf' in data and data['cpf'] and data['cpf'] != member.cpf:
            existing_member = Member.query.filter_by(cpf=data['cpf'].strip()).first()
            if existing_member and existing_member.id != id:
                app.logger.warning(f'CPF {data["cpf"]} already in use by member ID {existing_member.id} ({existing_member.name})')
                return jsonify({
                    'error': 'Este CPF já está em uso por outro membro',
                    'existingMemberId': existing_member.id,
                    'existingMemberName': existing_member.name
                }), 400
        
        # Check for duplicate email (if email is being updated)
        if 'email' in data and data['email'] and data['email'].strip().lower() != (member.email or '').lower():
            email = data['email'].strip().lower()
            existing_email = Member.query.filter(func.lower(Member.email) == email).first()
            if existing_email and existing_email.id != id:
                app.logger.warning(f'Email {email} already in use by member ID {existing_email.id} ({existing_email.name})')
                return jsonify({
                    'error': 'Este e-mail já está em uso por outro membro',
                    'existingMemberId': existing_email.id,
                    'existingMemberName': existing_email.name
                }), 400
        
        # Update member fields
        if 'name' in data:
            member.name = data['name'].strip()
            
        if 'email' in data:
            member.email = data['email'].strip().lower() if data['email'] else None
            
        if 'phone' in data:
            member.phone = data['phone'].strip() if data.get('phone') else None
            
        if 'birthDate' in data:
            if data['birthDate']:
                try:
                    member.birth_date = datetime.fromisoformat(data['birthDate']).date()
                except (ValueError, TypeError):
                    return jsonify({'error': 'Formato de data inválido. Use o formato AAAA-MM-DD'}), 400
            else:
                member.birth_date = None

        if 'conversion_date' in data:
            if data['conversion_date']:
                try:
                    member.date_conversion = datetime.fromisoformat(data['conversion_date']).date()
                except (ValueError, TypeError):
                    return jsonify({'error': 'Formato de data inválido. Use o formato AAAA-MM-DD'}), 400
            else:
                member.date_conversion = None


        if 'last_birthday_message' in data:
            if data['last_birthday_message']:
                try:
                    member.last_birthday_message_sent = datetime.fromisoformat(data['last_birthday_message']).date()
                except (ValueError, TypeError):
                    return jsonify({'error': 'Formato de data inválido. Use o formato AAAA-MM-DD'}), 400
            else:
                member.last_birthday_message_sent = None

                
        if 'address' in data:
            member.address = data['address'].strip() if data.get('address') else None
            
        # Update other fields
        fields_to_update = [
            'role', 'ministryTime', 'howFoundChurch', 'ministry', 'suggestions', 'sexo', 'status'
        ]
        
        for field in fields_to_update:
            if field in data:
                setattr(member, field.lower().replace('time', '_time').replace('found', '_found'), data[field])
        
        if 'isBaptized' in data:
            member.is_baptized = bool(data['isBaptized'])
            
        if 'ebdClassId' in data:
            member.ebd_class_id = data['ebdClassId'] if data['ebdClassId'] else None
            
        if 'cpf' in data:
            member.cpf = data['cpf'].strip()
        
        db.session.commit()
        return jsonify(member.to_dict())
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Erro ao atualizar membro ID {id}: {str(e)}', exc_info=True)
        return jsonify({'error': 'Erro ao atualizar o membro. Por favor, tente novamente.'}), 500


@app.route('/api/members/<int:id>', methods=['DELETE'])
def delete_member(id):
   member = Member.query.get_or_404(id)
   db.session.delete(member)
   db.session.commit()
   return '', 204


# ==================== ROUTES - TRANSACTIONS ====================


@app.route('/api/transactions', methods=['GET'])
def get_transactions():
   start_date = request.args.get('startDate')
   end_date = request.args.get('endDate')
   type_filter = request.args.get('type')
  
   query = Transaction.query
  
   if start_date:
       query = query.filter(Transaction.date >= datetime.fromisoformat(start_date).date())
   if end_date:
       query = query.filter(Transaction.date <= datetime.fromisoformat(end_date).date())
   if type_filter:
       query = query.filter_by(type=type_filter)
  
   transactions = query.order_by(Transaction.date.desc()).all()
   return jsonify([t.to_dict() for t in transactions])



@app.route('/api/transactions', methods=['POST'])
def create_transaction():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['type', 'category', 'amount', 'date']
        for field in required_fields:
            if field not in data or data[field] is None:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate amount is a positive number
        try:
            amount = float(data['amount'])
            if amount <= 0:
                return jsonify({'error': 'Amount must be greater than 0'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid amount format'}), 400
            
        # Create transaction
        transaction = Transaction(
            type=data['type'],
            category=data['category'],
            description=data.get('description', ''),
            amount=amount,
            date=datetime.fromisoformat(data['date']).date(),
            member_id=data.get('memberId')
        )
        
        # Add to session and commit
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify(transaction.to_dict()), 201
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': f'Invalid date format. Use ISO format (YYYY-MM-DD). Error: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error creating transaction: {str(e)}')
        return jsonify({'error': 'Failed to create transaction. Please try again.'}), 500


@app.route('/api/transactions/<int:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    try:
        # Busca a transação pelo ID
        transaction = Transaction.query.get_or_404(transaction_id)
        
        # Remove a transação do banco de dados
        db.session.delete(transaction)
        db.session.commit()
        
        return jsonify({'message': 'Transação excluída com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Erro ao excluir transação {transaction_id}: {str(e)}')
        return jsonify({'error': 'Falha ao excluir a transação. Por favor, tente novamente.'}), 500


@app.route('/api/transactions/summary', methods=['GET'])
def get_financial_summary():
   from sqlalchemy import func
  
   income = db.session.query(func.sum(Transaction.amount)).filter_by(type='income').scalar() or 0
   expense = db.session.query(func.sum(Transaction.amount)).filter_by(type='expense').scalar() or 0
  
   return jsonify({
       'income': float(income),
       'expense': float(expense),
       'balance': float(income - expense)
   })


# ==================== ROUTES - ATTENDANCE ====================


@app.route('/api/attendance', methods=['GET'])
def get_attendance():
   date = request.args.get('date')
   service_type = request.args.get('serviceType')
  
   query = Attendance.query
   if date:
       query = query.filter_by(date=datetime.fromisoformat(date).date())
   if service_type:
       query = query.filter_by(service_type=service_type)
  
   attendances = query.all()
   return jsonify([a.to_dict() for a in attendances])


@app.route('/api/attendance', methods=['POST'])
def create_attendance():
   data = request.get_json()
  
   # Verificar se já existe registro
   existing = Attendance.query.filter_by(
       member_id=data.get('memberId'),
       date=datetime.fromisoformat(data.get('date')).date(),
       service_type=data.get('serviceType')
   ).first()
  
   if existing:
       existing.present = data.get('present', False)
       db.session.commit()
       return jsonify(existing.to_dict())
  
   attendance = Attendance(
       member_id=data.get('memberId'),
       date=datetime.fromisoformat(data.get('date')).date(),
       present=data.get('present', False),
       service_type=data.get('serviceType')
   )
  
   db.session.add(attendance)
   db.session.commit()
  
   return jsonify(attendance.to_dict()), 201


# ==================== ROUTES - EBD CLASSES ====================


@app.route('/api/ebd-classes', methods=['GET'])
def get_ebd_classes():
   classes = EBDClass.query.all()
   return jsonify([c.to_dict() for c in classes])


@app.route('/api/ebd-classes/<int:id>/members', methods=['GET'])
def get_ebd_class_members(id):
   ebd_class = EBDClass.query.get_or_404(id)
   members = Member.query.filter_by(ebd_class_id=id).all()
   return jsonify({
       'class': ebd_class.to_dict(),
       'members': [m.to_dict() for m in members]
   })




@app.route('/api/ebd-classes/<int:id>', methods=['DELETE'])
def delete_ebd_class(id):
   ebd_class = EBDClass.query.get_or_404(id)
  
   db.session.delete(ebd_class)
   db.session.commit()
  
   return '', 204




@app.route('/api/ebd-classes', methods=['POST'])
def create_ebd_class():
   data = request.get_json()


   # Validação mínima
   if not data or 'name' not in data or 'password' not in data:
       return jsonify({'error': 'name e password são obrigatórios'}), 400


   # Gerar slug automaticamente se não vier
   slug = data.get('slug') or slugify(data['name'])


   # Verificar se o slug já existe
   if EBDClass.query.filter_by(slug=slug).first():
       return jsonify({'error': 'slug já existe'}), 400


   # Gerar hash da senha
   hashed_password = generate_password_hash(data['password'])


   ebd_class = EBDClass(
       name=data['name'],
       slug=slug,
       password=hashed_password,
       created_at=datetime.utcnow()
   )


   db.session.add(ebd_class)
   db.session.commit()


   return jsonify(ebd_class.to_dict()), 201








@app.route('/api/ebd-classes/verify', methods=['POST'])
def verify_ebd_class():
   data = request.get_json()


   # Validar entrada
   if not data or 'slug' not in data or 'password' not in data:
       return jsonify({'error': 'slug e password são obrigatórios'}), 400


   # Buscar classe
   ebd_class = EBDClass.query.filter_by(slug=data['slug']).first()


   if not ebd_class:
       return jsonify({'error': 'Classe não encontrada'}), 404


   # Verificar senha
   if not check_password_hash(ebd_class.password, data['password']):
       return jsonify({'error': 'Senha incorreta'}), 401


   # Autenticado com sucesso
   return jsonify({
       'message': 'Autenticado com sucesso',
       'class': ebd_class.to_dict()
   }), 200




@app.route('/api/ebd-classes/<int:id>', methods=['PUT'])
def update_ebd_class(id):
   data = request.get_json()
  
   ebd_class = EBDClass.query.get_or_404(id)


   # atualizar nome
   if 'name' in data and data['name']:
       ebd_class.name = data['name']


   # atualizar slug
   if 'slug' in data and data['slug']:
       new_slug = data['slug']


       # verificar slug duplicado
       slug_exists = EBDClass.query.filter(
           EBDClass.slug == new_slug,
           EBDClass.id != id
       ).first()


       if slug_exists:
           return jsonify({'error': 'slug já está em uso por outra classe'}), 400
      
       ebd_class.slug = new_slug
   elif 'name' in data:
       # se quiser gerar slug automaticamente ao editar o nome:
       ebd_class.slug = slugify(data['name'])


   # atualizar senha
   if 'password' in data and data['password']:
       ebd_class.password = generate_password_hash(data['password'])


   db.session.commit()


   return jsonify(ebd_class.to_dict()), 200




 
# ==================== ROUTES - MINISTRIES ====================


#@app.route('/api/ministries', methods=['GET'])
#def get_ministries():
#    ministries = Ministry.query.all()
#    return jsonify([m.to_dict() for m in ministries])






# Add this route to list all ministries
@app.route('/api/ministries', methods=['GET'])
def get_ministries():
    try:
        ministries = Ministry.query.all()
        return jsonify([{
            'id': m.id,
            'name': m.name,
            'description': m.description,
            'created_at': m.created_at.isoformat() if m.created_at else None
        } for m in ministries])
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar ministérios: {str(e)}'}), 500




# -----------------------------
# POST - CRIAR NOVO
# -----------------------------
@app.route('/api/ministries', methods=['POST'])
def create_ministry():
   data = request.get_json()


   # validar nome obrigatório
   if not data.get('name'):
       return jsonify({'error': 'O campo name é obrigatório'}), 400


   ministry = Ministry(
       name=data['name'],
       description=data.get('description'),
       created_at=datetime.utcnow()
   )


   db.session.add(ministry)
   db.session.commit()


   return jsonify(ministry.to_dict()), 201




# -----------------------------
# PUT - ATUALIZAR
# -----------------------------
@app.route('/api/ministries/<int:id>', methods=['PUT'])
def update_ministry(id):
   data = request.get_json()
   ministry = Ministry.query.get_or_404(id)


   for key, value in data.items():
       if hasattr(ministry, key):
           setattr(ministry, key, value)


   db.session.commit()


   return jsonify(ministry.to_dict()), 200






# -----------------------------
# DELETE - EXCLUIR
# -----------------------------
@app.route('/api/ministries/<int:id>', methods=['DELETE'])
def delete_ministry(id):
   ministry = Ministry.query.get_or_404(id)


   db.session.delete(ministry)
   db.session.commit()


   return '', 204






# ==================== ROUTES - AUTH ====================






@app.route('/api/users', methods=['GET'])
def get_all_users():
   try:
       users = User.query.all()
       return jsonify([user.to_dict() for user in users]), 200
   except Exception as e:
       return jsonify({'error': str(e)}), 500




      


@app.route('/api/auth/login', methods=['POST'])
def login_user():
   data = request.get_json()
   print("chegou")
   print(data)

   if not data:
       return jsonify({'error': 'JSON inválido'}), 400


   username = data.get('username')
   password = data.get('password')


   if not username or not password:
       return jsonify({'error': 'username e password são obrigatórios'}), 400


   # Buscar usuário no banco
   user = User.query.filter_by(username=username).first()


   if not user:
       return jsonify({'error': 'Usuário não encontrado'}), 401


   # Validar senha (scrypt)
   if not user.check_password(password):
       return jsonify({'error': 'Senha incorreta'}), 401


   # Login OK
   return jsonify({
       "success": True,
       "message": "Login realizado com sucesso",
       "user": user.to_dict()
   }), 200








#--teste--


# Mapeamento de roles
ROLE_MAP = {
   "Administrador Geral": 1,
   "Líder de Ministério": 2,
   "Secretário": 3
}


@app.route('/api/users', methods=['POST'])
def create_user():
   data = request.get_json()


   if not data:
       return jsonify({'error': 'JSON body is required'}), 400


   username = data.get('username')
   password = data.get('password')
   role_name = data.get('role')  # Nome da role vindo do frontend


   # Validação básica
   if not username or not password or not role_name:
       return jsonify({'error': 'username, password e role são obrigatórios'}), 400


   # Verifica duplicidade
   if User.query.filter_by(username=username).first():
       return jsonify({'error': 'Usuário já existe'}), 409


   # Converte o role para id
   role_id = ROLE_MAP.get(role_name)
   if not role_id:
       return jsonify({'error': f'Role inválida: {role_name}'}), 400


   # Verifica se o role_id existe na tabela roles
   role = Role.query.get(role_id)
   if not role:
       return jsonify({'error': f'Role ID {role_id} não existe no banco'}), 400


   # Criar usuário
   user = User(
       username=username,
       role_id=role_id
   )
   user.set_password(password)


   db.session.add(user)
   db.session.commit()


   return jsonify({
       'message': 'Usuário criado com sucesso',
       'user': user.to_dict()
   }), 201






@app.route('/api/users/<int:id>', methods=['PUT'])
def update_user(id):


   # Resposta obrigatória ao OPTIONS
   if request.method == 'OPTIONS':
       response = jsonify({'status': 'ok'})
       response.headers.add("Access-Control-Allow-Origin", "*")
       response.headers.add("Access-Control-Allow-Methods", "PUT")
       response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
       return response, 200


   # PUT (edição normal)
   user = User.query.get_or_404(id)
   data = request.get_json() or {}


   if 'username' in data:
       exists = User.query.filter(
           User.username == data['username'],
           User.id != id
       ).first()


       if exists:
           return jsonify({'error': 'Este username já está em uso'}), 400


       user.username = data['username']


   if 'password' in data and data['password']:
       user.password_hash = generate_password_hash(data['password'])


   if 'role_id' in data:
       user.role_id = data['role_id']


   db.session.commit()


   return jsonify({
       'success': True,
       'message': 'Usuário atualizado com sucesso',
       'user': user.to_dict()
   }), 200








@app.route('/api/users/<int:id>', methods=['DELETE', 'OPTIONS'])
def delete_user(id):


   # Responder o preflight OPTIONS
   if request.method == 'OPTIONS':
       response = jsonify({'status': 'ok'})
       response.headers.add("Access-Control-Allow-Origin", "*")
       response.headers.add("Access-Control-Allow-Methods", "DELETE, OPTIONS")
       response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
       return response, 200


   # DELETE normal
   user = User.query.get_or_404(id)


   db.session.delete(user)
   db.session.commit()


   response = jsonify({'success': True, 'message': 'Usuário removido com sucesso'})
   response.headers.add("Access-Control-Allow-Origin", "*")
   return response, 200



# ==================== ROUTES - APP CONFIG ====================

@app.route('/api/config', methods=['GET'])
def get_config():
    config = AppConfig.query.first()
    if config is None:
        return jsonify({
            'message': 'No configuration found',
            'data': None
        }), 404
    
    return jsonify({
        'message': 'Configuration retrieved successfully',
        'data': config.to_dict()
    }), 200

@app.route('/api/config', methods=['POST'])
def create_or_update_config():
    data = request.get_json()
    print(data)
    # Validate required fields
    required_fields = ['weeklySchedule', 'consolidationStages']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'message': f'Missing required field: {field}'
            }), 400

    config = AppConfig.query.first()
    
    if config is None:
        # Create new config
        config = AppConfig(
            weekly_schedule=data['weeklySchedule'],
            slides=data.get('slides', []),
            slide_interval=data.get('slideInterval', 5000),
            consolidation_stages=data['consolidationStages'],
            welcome_message_new_convert=data.get('welcomeMessageNewConvert'),
            welcome_message_regular_member=data.get('welcomeMessageRegularMember'),
            evolution_api_url=data.get('evolutionApiUrl'),
            evolution_api_key=data.get('evolutionApiKey'),
            evolution_instance_name=data.get('evolutionInstanceName'),
            birthday_message_enabled=data.get('birthdayMessageEnabled', False),
            birthday_message_time=data.get('birthdayMessageTime'),
            birthday_message_template=data.get('birthdayMessageTemplate'),
            birthday_auto_send=data.get('birthdayAutoSend', False),
            birthday_auto_time=data.get('birthdayAutoTime'),
            contact_address=data.get('contactAddress'),
            contact_phone=data.get('contactPhone'),
            social_instagram=data.get('socialInstagram'),
            social_facebook=data.get('socialFacebook'),
            social_youtube=data.get('socialYoutube')           
        )
        db.session.add(config)
    else:
        # Update existing config
        config.weekly_schedule = data['weeklySchedule']
        config.slides = data.get('slides', [])
        config.slide_interval = data.get('slideInterval', 5000)
        config.consolidation_stages = data['consolidationStages']
        config.welcome_message_new_convert = data.get('welcomeMessageNewConvert')
        config.welcome_message_regular_member = data.get('welcomeMessageRegularMember')
        config.evolution_api_url = data.get('evolutionApiUrl')
        config.evolution_api_key = data.get('evolutionApiKey')
        config.evolution_instance_name = data.get('evolutionInstanceName')
        config.birthday_message_enabled = data.get('birthdayMessageEnabled', False)
        config.birthday_message_time = data.get('birthdayMessageTime')
        config.birthday_message_template = data.get('birthdayMessageTemplate')
        config.birthday_auto_send = data.get('birthdayAutoSend', False)
        config.birthday_auto_time=data.get('birthdayAutoTime')

        config.contact_address=data.get('contactAddress')
        config.contact_phone=data.get('contactPhone')
        config.social_instagram=data.get('socialInstagram')
        config.social_facebook=data.get('socialFacebook')
        config.social_youtube=data.get('socialYoutube')  
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Configuration saved successfully',
            'data': config.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'message': f'Error saving configuration: {str(e)}'
        }), 500


# ==================== CHURCH MINISTRY MODELS ====================

class ChurchMinistry(db.Model):
    __tablename__ = 'church_ministries'
    
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    schedule = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    posts = db.relationship('MinistryPost', backref='ministry', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'ministryName': self.name,
            'description': self.description,
            'schedule': self.schedule,
            'posts': [post.to_dict() for post in self.posts] if self.posts else [],
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }

class MinistryPost(db.Model):
    __tablename__ = 'ministry_posts'
    
    id = db.Column(db.String(50), primary_key=True)
    ministry_id = db.Column(db.String(50), db.ForeignKey('church_ministries.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(200))
    content = db.Column(db.JSON, nullable=True)  # Can store text, array of text, or base64 image
    description = db.Column(db.Text)
    type = db.Column(db.String(50), nullable=False)  # 'event', 'article', 'photo', etc.
    date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'description': self.description,
            'type': self.type,
            'date': self.date.isoformat() if self.date else None
        }


# ==================== ROUTES - STATISTICS ====================


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
   from sqlalchemy import func
  
   stats = {
       'totalMembers': Member.query.count(),
       'baptizedMembers': Member.query.filter_by(is_baptized=True).count(),
       'totalClasses': EBDClass.query.count(),
       'totalMinistries': Ministry.query.count(),
       'membersByMinistry': db.session.query(
           Member.ministry, func.count(Member.id)
       ).group_by(Member.ministry).all()
   }
  
   return jsonify(stats)


# ==================== HEALTH CHECK ====================


@app.route('/api/health', methods=['GET'])
def health_check():
   try:
       # Testar conexão com banco
       db.session.execute('SELECT 1')
       return jsonify({
           'status': 'ok',
           'message': 'API está funcionando',
           'database': 'conectado'
       })
   except Exception as e:
       return jsonify({
           'status': 'error',
           'message': str(e)
       }), 500






# ==================== ROUTER USER ====================



# ==================== ROUTES - CHURCHES ====================

@app.route('/api/churches', methods=['GET'])
def get_churches():
    try:
        churches = Church.query.all()
        return jsonify([church.to_dict() for church in churches])
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar igrejas: {str(e)}'}), 500

@app.route('/api/churches/<church_id>', methods=['GET'])
def get_church(church_id):
    try:
        church = Church.query.get(church_id)
        if not church:
            return jsonify({'error': 'Igreja não encontrada'}), 404
        return jsonify(church.to_dict())
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar igreja: {str(e)}'}), 500

@app.route('/api/churches', methods=['POST'])
def create_church():
    try:
        data = request.json
        if not data.get('name'):
            return jsonify({'error': 'O nome da igreja é obrigatório'}), 400

        # Gera um ID único para a igreja
        church_id = f"church-{int(time.time() * 1000)}"
        
        # Cria a igreja
        church = Church(
            id=church_id,
            name=data['name']
        )
        db.session.add(church)

        # Adiciona os horários, se fornecidos
        if 'schedule' in data and isinstance(data['schedule'], list):
            for schedule_item in data['schedule']:
                schedule = ChurchSchedule(
                    id=f"sch-{int(time.time() * 1000)}",
                    church_id=church_id,
                    day=schedule_item.get('day', ''),
                    title=schedule_item.get('title', ''),
                    description=schedule_item.get('description', ''),
                    time=schedule_item.get('time', '00:00')
                )
                db.session.add(schedule)

        db.session.commit()
        return jsonify(church.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao criar igreja: {str(e)}'}), 500

@app.route('/api/churches/<church_id>', methods=['PUT'])
def update_church(church_id):
    try:
        church = Church.query.get(church_id)
        if not church:
            return jsonify({'error': 'Igreja não encontrada'}), 404

        data = request.json

        # Atualiza o nome se fornecido
        if 'name' in data:
            church.name = data['name']

        # Remove todos os horários existentes
        ChurchSchedule.query.filter_by(church_id=church_id).delete()

        # Adiciona os novos horários, se fornecidos
        if 'schedule' in data and isinstance(data['schedule'], list):
            for schedule_item in data['schedule']:
                schedule = ChurchSchedule(
                    id=f"sch-{int(time.time() * 1000)}",
                    church_id=church_id,
                    day=schedule_item.get('day', ''),
                    title=schedule_item.get('title', ''),
                    description=schedule_item.get('description', ''),
                    time=schedule_item.get('time', '00:00')
                )
                db.session.add(schedule)
        
        db.session.commit()
        return jsonify(church.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao atualizar igreja: {str(e)}'}), 500

@app.route('/api/churches/<church_id>/schedules', methods=['GET'])
def get_church_schedules(church_id):
    try:
        # Verifica se a igreja existe
        church = Church.query.get_or_404(church_id)
        
        # Retorna os horários da igreja
        schedules = ChurchSchedule.query.filter_by(church_id=church_id).all()
        return jsonify([{
            'id': s.id,
            'day': s.day,
            'title': s.title,
            'description': s.description,
            'time': s.time
        } for s in schedules])
        
    except Exception as e:
        app.logger.error(f'Erro ao buscar horários da igreja {church_id}: {str(e)}')
        return jsonify({'error': 'Falha ao buscar horários'}), 500

@app.route('/api/churches/<church_id>/schedules', methods=['POST'])
def add_church_schedule(church_id):
    try:
        # Verifica se a igreja existe
        church = Church.query.get_or_404(church_id)
        
        data = request.json
        
        # Validação dos campos obrigatórios
        required_fields = ['day', 'title', 'time']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'O campo {field} é obrigatório'}), 400
        
        # Cria o novo horário
        schedule = ChurchSchedule(
            id=f"sch-{int(time.time() * 1000)}",
            church_id=church_id,
            day=data['day'],
            title=data['title'],
            description=data.get('description', ''),
            time=data['time']
        )
        
        db.session.add(schedule)
        db.session.commit()
        
        return jsonify({
            'id': schedule.id,
            'day': schedule.day,
            'title': schedule.title,
            'description': schedule.description,
            'time': schedule.time
        }), 201
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Erro ao adicionar horário à igreja {church_id}: {str(e)}')
        return jsonify({'error': 'Falha ao adicionar horário'}), 500

@app.route('/api/churches/<church_id>/schedules/<schedule_id>', methods=['PUT'])
def update_church_schedule(church_id, schedule_id):
    try:
        # Busca o horário específico da igreja
        schedule = ChurchSchedule.query.filter_by(
            id=schedule_id,
            church_id=church_id
        ).first_or_404()
        
        data = request.json
        
        # Atualiza os campos fornecidos
        if 'day' in data:
            schedule.day = data['day']
        if 'title' in data:
            schedule.title = data['title']
        if 'description' in data:
            schedule.description = data['description']
        if 'time' in data:
            schedule.time = data['time']
        
        db.session.commit()
        
        return jsonify({
            'id': schedule.id,
            'day': schedule.day,
            'title': schedule.title,
            'description': schedule.description,
            'time': schedule.time
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Erro ao atualizar horário {schedule_id}: {str(e)}')
        return jsonify({'error': 'Falha ao atualizar horário'}), 500

@app.route('/api/churches/<church_id>/schedules/<schedule_id>', methods=['DELETE'])
def delete_church_schedule(church_id, schedule_id):
    try:
        # Busca o horário específico da igreja
        schedule = ChurchSchedule.query.filter_by(
            id=schedule_id,
            church_id=church_id
        ).first_or_404()
        
        db.session.delete(schedule)
        db.session.commit()
        
        return '', 204
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Erro ao excluir horário {schedule_id}: {str(e)}')
        return jsonify({'error': 'Falha ao excluir horário'}), 500

@app.route('/api/churches/<church_id>', methods=['DELETE'])
def delete_church(church_id):
    try:
        church = Church.query.get(church_id)
        if not church:
            return jsonify({'error': 'Igreja não encontrada'}), 404

        # A exclusão em cascata vai remover os horários automaticamente
        db.session.delete(church)
        db.session.commit()
        return '', 204

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao excluir igreja: {str(e)}'}), 500




# ==================== ROUTES - APP CONFIG ====================



# ==================== ROUTES - ABOUT US ====================

@app.route('/api/about-us', methods=['GET'])
def get_about_us():
   about = AboutUs.query.first()
   if about:
       return jsonify(about.to_dict())
   return jsonify({'message': 'Informações não encontradas'}), 404




# ==================== ROUTES - ROLES ====================

# Listar todas as funções
@app.route('/api/roles', methods=['GET'])
def get_roles():
    try:
        roles = Role.query.all()
        return jsonify([{
            'id': role.id,
            'name': role.name,
            'is_system': role.is_system,
            'permissions': role.permissions if role.permissions else []
        } for role in roles])
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar funções: {str(e)}'}), 500

# Obter uma função específica
@app.route('/api/roles/<role_name>', methods=['GET'])
def get_role(role_name):
    try:
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            return jsonify({'error': 'Função não encontrada'}), 404
            
        return jsonify({
            'id': role.id,
            'name': role.name,
            'is_system': role.is_system,
            'permissions': role.permissions if role.permissions else []
        })
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar função: {str(e)}'}), 500


# Coloque esta função auxiliar no início do arquivo, logo após as importações
def update_role_map():
    """Atualiza o ROLE_MAP com as funções atuais do banco de dados"""
    roles = Role.query.all()
    role_map = {role.name: role.id for role in roles}
    # Atualiza o ROLE_MAP global
    globals()['ROLE_MAP'] = role_map
    return role_map

# Modifique a rota de criação de função
@app.route('/api/roles', methods=['POST'])
def create_role():
    try:
        data = request.json
        if not data.get('name'):
            return jsonify({'error': 'O nome da função é obrigatório'}), 400

        # Verifica se a função já existe
        if Role.query.filter_by(name=data['name']).first():
            return jsonify({'error': 'Já existe uma função com este nome'}), 400

        new_role = Role(
            name=data['name'],
            is_system=data.get('is_system', False),
            permissions=data.get('permissions', [])
        )

        db.session.add(new_role)
        db.session.commit()
        
        # Atualiza o ROLE_MAP após criar uma nova função
        update_role_map()

        return jsonify({
            'id': new_role.id,
            'name': new_role.name,
            'is_system': new_role.is_system,
            'permissions': new_role.permissions if new_role.permissions else []
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao criar função: {str(e)}'}), 500

# Adicione também na inicialização do aplicativo para carregar os valores iniciais
# Coloque isso logo após a criação do app
with app.app_context():
    try:
        update_role_map()
    except:
        pass  # Ignora erros durante a inicialização
# Atualizar função existente
@app.route('/api/roles/<role_identifier>', methods=['PUT'])
def update_role(role_identifier):
    try:
        # Tenta encontrar por ID
        if role_identifier.isdigit():
            role = Role.query.get(int(role_identifier))
        else:
            # Se não for um número, tenta encontrar pelo nome
            role = Role.query.filter_by(name=role_identifier).first()

        if not role:
            return jsonify({'error': 'Função não encontrada'}), 404

        data = request.get_json()

        # Atualiza o nome se fornecido e diferente
        if 'name' in data and data['name'] != role.name:
            # Verifica se já existe outra função com o novo nome
            if Role.query.filter(Role.name == data['name'], Role.id != role.id).first():
                return jsonify({'error': 'Já existe uma função com este nome'}), 400
            role.name = data['name']

        # Atualiza as permissões se fornecidas
        if 'permissions' in data:
            role.permissions = data['permissions']

        # Não permite alterar is_system via API
        if 'is_system' in data:
            del data['is_system']

        db.session.commit()

        return jsonify({
            'id': role.id,
            'name': role.name,
            'is_system': role.is_system,
            'permissions': role.permissions if role.permissions else []
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao atualizar função: {str(e)}'}), 500

# Excluir função
@app.route('/api/roles/<role_identifier>', methods=['DELETE'])
def delete_role(role_identifier):
    try:
        # Tenta encontrar por ID
        if role_identifier.isdigit():
            role = Role.query.get(int(role_identifier))
        else:
            # Se não for um número, tenta encontrar pelo nome
            role = Role.query.filter_by(name=role_identifier).first()

        if not role:
            return jsonify({'error': 'Função não encontrada'}), 404

        # Não permite excluir funções do sistema
        if role.is_system:
            return jsonify({'error': 'Não é possível excluir funções do sistema'}), 403

        # Verifica se existem usuários com esta função
        if User.query.filter_by(role_id=role.id).count() > 0:
            return jsonify({
                'error': 'Não é possível excluir uma função que está sendo usada por usuários'
            }), 400

        db.session.delete(role)
        db.session.commit()

        return '', 204

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao excluir função: {str(e)}'}), 500




# ==================== CHURCH MINISTRY ROUTES ====================

@app.route('/api/church_ministries', methods=['GET'])
def get_church_ministries():
    ministries = ChurchMinistry.query.all()
    return jsonify([m.to_dict() for m in ministries])

@app.route('/api/church_ministries/<ministry_id>', methods=['GET'])
def get_church_ministry(ministry_id):
    ministry = ChurchMinistry.query.get_or_404(ministry_id)
    return jsonify(ministry.to_dict())

@app.route('/api/church_ministries', methods=['POST'])
def create_church_ministry():
    data = request.get_json()
    
    # Generate a unique ID
    ministry_id = f"ministry_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
    
    ministry = ChurchMinistry(
        id=ministry_id,
        name=data.get('ministryName', ''),
        description=data.get('description', ''),
        schedule=data.get('schedule', '')
    )
    
    # Add posts if provided
    posts_data = data.get('posts', [])
    for post_data in posts_data:
        post_id = f"post_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
        post = MinistryPost(
            id=post_id,
            ministry_id=ministry_id,
            title=post_data.get('title', ''),
            content=post_data.get('content', ''),
            description=post_data.get('description', ''),
            type=post_data.get('type', 'article'),
            date=datetime.fromisoformat(post_data.get('date')) if post_data.get('date') else datetime.utcnow()
        )
        ministry.posts.append(post)
    
    db.session.add(ministry)
    db.session.commit()
    
    return jsonify(ministry.to_dict()), 201

@app.route('/api/church_ministries/<ministry_id>', methods=['PUT'])
def update_church_ministry(ministry_id):
    ministry = ChurchMinistry.query.get_or_404(ministry_id)
    data = request.get_json()
    
    # Update ministry fields
    if 'ministryName' in data:
        ministry.name = data['ministryName']
    if 'description' in data:
        ministry.description = data['description']
    if 'schedule' in data:
        ministry.schedule = data['schedule']
    
    # Update or add posts
    if 'posts' in data:
        # Delete existing posts not in the new data
        existing_post_ids = {post.id for post in ministry.posts}
        new_post_ids = {post.get('id') for post in data['posts'] if post.get('id')}
        posts_to_delete = existing_post_ids - new_post_ids
        
        for post_id in posts_to_delete:
            post = MinistryPost.query.get(post_id)
            if post:
                db.session.delete(post)
        
        # Update or add posts
        for post_data in data['posts']:
            if 'id' in post_data and post_data['id'] in existing_post_ids:
                # Update existing post
                post = next((p for p in ministry.posts if p.id == post_data['id']), None)
                if post:
                    post.title = post_data.get('title', post.title)
                    post.content = post_data.get('content', post.content)
                    post.description = post_data.get('description', post.description)
                    post.type = post_data.get('type', post.type)
                    if 'date' in post_data:
                        post.date = datetime.fromisoformat(post_data['date'])
            else:
                # Add new post
                post_id = f"post_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
                post = MinistryPost(
                    id=post_id,
                    ministry_id=ministry_id,
                    title=post_data.get('title', ''),
                    content=post_data.get('content', ''),
                    description=post_data.get('description', ''),
                    type=post_data.get('type', 'article'),
                    date=datetime.fromisoformat(post_data['date']) if 'date' in post_data else datetime.utcnow()
                )
                ministry.posts.append(post)
    
    db.session.commit()
    return jsonify(ministry.to_dict())

@app.route('/api/church_ministries/<ministry_id>', methods=['DELETE'])
def delete_church_ministry(ministry_id):
    ministry = ChurchMinistry.query.get_or_404(ministry_id)
    db.session.delete(ministry)
    db.session.commit()
    return '', 204

# Individual post endpoints
@app.route('/api/church_ministries/<ministry_id>/posts', methods=['POST'])
def create_ministry_post(ministry_id):
    ministry = ChurchMinistry.query.get_or_404(ministry_id)
    data = request.get_json()
    
    post_id = f"post_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
    post = MinistryPost(
        id=post_id,
        ministry_id=ministry_id,
        title=data.get('title', ''),
        content=data.get('content', ''),
        description=data.get('description', ''),
        type=data.get('type', 'article'),
        date=datetime.fromisoformat(data['date']) if 'date' in data else datetime.utcnow()
    )
    
    db.session.add(post)
    db.session.commit()
    
    return jsonify(post.to_dict()), 201

@app.route('/api/ministry_posts/<post_id>', methods=['PUT'])
def update_ministry_post(post_id):
    post = MinistryPost.query.get_or_404(post_id)
    data = request.get_json()
    
    if 'title' in data:
        post.title = data['title']
    if 'content' in data:
        post.content = data['content']
    if 'description' in data:
        post.description = data['description']
    if 'type' in data:
        post.type = data['type']
    if 'date' in data:
        post.date = datetime.fromisoformat(data['date'])
    
    db.session.commit()
    return jsonify(post.to_dict())

@app.route('/api/ministry_posts/<post_id>', methods=['DELETE'])
def delete_ministry_post(post_id):
    post = MinistryPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    return '', 204





@app.route('/api/birthdays/process', methods=['POST'])
def process_birthdays():
    
    try:
        today = datetime.now().date()
        today_month_day = (today.month, today.day)
        
        # Get app config for API settings
        config = AppConfig.query.first()
        if not config:
            return jsonify({
                'success': False,
                'message': 'App configuration not found'
            }), 500
        
        # Find members with birthday today
        members = Member.query.filter(
            and_(
                extract('month', Member.birthDate) == today_month_day[0],
                extract('day', Member.birthDate) == today_month_day[1],
                (Member.last_birthday_message_sent != today) | (Member.last_birthday_message_sent.is_(None))
            )
        ).all()
        
        if not members:
            return jsonify({
                'success': True,
                'message': 'No birthdays to process today'
            })
        
        # Prepare API request data
        headers = {
            'Content-Type': 'application/json',
            'apikey': config.evolution_api_key
        }
        
        success_count = 0
        
        for member in members:
            try:
                # Skip if no phone number or birthday
                if not member.phone or not member.birthDate:
                    continue
                
                # Format message with member's name
                message = f"Feliz aniversário, {member.name}! 🎉\n\n{config.birthday_message_template or 'Desejamos um dia abençoado!'}"
                
                # Prepare request data for Evolution API
                payload = {
                    "number": member.phone,
                    "textMessage": {
                        "text": message
                    }
                }
                
                # Send message via Evolution API
                response = requests.post(
                    f"{config.evolution_api_url}/message/sendText/{config.evolution_instance_name}",
                    json=payload,
                    headers=headers
                )
                
                # If message sent successfully, update the member's record
                if response.status_code in (200, 201):
                    member.last_birthday_message_sent = today
                    db.session.add(member)
                    success_count += 1
                
            except Exception as e:
                print(f"Error sending message to {member.phone}: {str(e)}")
                continue
        
        # Commit all updates at once
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully sent {success_count} birthday messages'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error processing birthdays: {str(e)}'
        }), 500






@app.route('/api/birthdays/today', methods=['GET'])
def get_todays_birthdays():

    
    try:
        today = datetime.now().date()
        today_month_day = (today.month, today.day)
        
        members = Member.query.filter(
            and_(
                extract('month', Member.birthDate) == today_month_day[0],
                extract('day', Member.birthDate) == today_month_day[1]
            )
        ).all()

        print(members)
        
        return jsonify({
            'success': True,
            'data': [{
                'id': m.id,
                'name': m.name,
                'phone': m.phone,
                'birthday': m.birthDate.isoformat() if m.birthday else None,
                'last_message_sent': m.last_birthday_message_sent.isoformat() if m.last_birthday_message_sent else None
            } for m in members]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching birthdays: {str(e)}'
        }), 500




class Slide(db.Model):
    __tablename__ = 'homepage_slides'
    id = db.Column(db.String(50), primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    image_url = db.Column(db.Text(length=4294967295))  # LONGTEXT equivalent
    button_text = db.Column(db.String(50))
    link_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'image_url': self.image_url,
            'button_text': self.button_text,
            'link_url': self.link_url,
            'is_active': self.is_active
        }

@app.route('/api/config/slides', methods=['GET'])
def get_slides():
    try:
        slides = Slide.query.filter_by(is_active=True).all()
        return jsonify({
            'success': True,
            'data': [slide.to_dict() for slide in slides]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/config/slides', methods=['POST'])
def sync_slides():
    data = request.get_json()
    slides_data = data.get('homepage_slides', [])
    
    try:
        # 1. Limpa os slides antigos (ou implemente lógica de merge)
        Slide.query.delete()
        
        # 2. Insere os novos vindos do frontend
        for s in slides_data:
            new_slide = Slide(
                id=s['id'],
                title=s['title'],
                description=s['description'],
                image_url=s['image_url'],
                button_text=s['button_text'],
                link_url=s['link_url'],
                is_active=bool(s.get('is_active', True))  # Default to True if not provided
            )
            db.session.add(new_slide)
            
        db.session.commit()
        return jsonify({
            "success": True, 
            "message": f"{len(slides_data)} slides sincronizados."
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False, 
            "message": str(e)
        }), 500

# ==================== ERROR HANDLERS ====================


@app.errorhandler(404)
def not_found(error):
   return jsonify({'error': 'Recurso não encontrado'}), 404


@app.errorhandler(500)
def internal_error(error):
   db.session.rollback()
   return jsonify({'error': 'Erro interno do servidor'}), 500


if __name__ == '__main__':
   app.run(debug=True, host='0.0.0.0', port=5000)
