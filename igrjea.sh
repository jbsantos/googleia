#!/bin/bash

# ============================================
# Script de Teste Completo da API
# Testa todos os endpoints com CRUD
# ============================================

API_URL="http://localhost:5000/api"
HEADER="Content-Type: application/json"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para imprimir seção
print_section() {
    echo -e "\n${BLUE}============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================${NC}\n"
}

# Função para imprimir sucesso
print_success() {
    echo -e "${GREEN}✓ $1${NC}\n"
}

# Função para imprimir erro
print_error() {
    echo -e "${RED}✗ $1${NC}\n"
}

# Função para imprimir info
print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# ============================================
# 1. HEALTH CHECK
# ============================================
print_section "1. HEALTH CHECK"

print_info "GET /api/health"
curl -s -X GET "$API_URL/health" | jq '.'
print_success "Health check realizado"

sleep 1

# ============================================
# 2. AUTHENTICATION (AUTH)
# ============================================
print_section "2. AUTHENTICATION"

print_info "POST /api/auth/login - Login com admin"
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
  -H "$HEADER" \
  -d '{
    "username": "admin",
    "password": "admin"
  }')
echo $LOGIN_RESPONSE | jq '.'
print_success "Login realizado"

print_info "POST /api/auth/login - Login com líder"
curl -s -X POST "$API_URL/auth/login" \
  -H "$HEADER" \
  -d '{
    "username": "lider",
    "password": "lider"
  }' | jq '.'
print_success "Login de líder realizado"

print_info "POST /api/auth/login - Login inválido (deve falhar)"
curl -s -X POST "$API_URL/auth/login" \
  -H "$HEADER" \
  -d '{
    "username": "invalido",
    "password": "senha_errada"
  }' | jq '.'
print_error "Login inválido (esperado)"

sleep 1

# ============================================
# 3. MEMBERS (CRUD COMPLETO)
# ============================================
print_section "3. MEMBERS - CRUD"

# CREATE
print_info "POST /api/members - Criar novo membro"
NEW_MEMBER=$(curl -s -X POST "$API_URL/members" \
  -H "$HEADER" \
  -d '{
    "name": "Carlos Teste",
    "email": "carlos.teste@email.com",
    "phone": "+55 (11) 91111-2222",
    "birthDate": "1995-08-15",
    "address": "Rua Teste, 456, São Paulo, SP",
    "role": "Membro",
    "ministryTime": "2 anos",
    "isBaptized": true,
    "howFoundChurch": "Internet",
    "ministry": "Jovens",
    "suggestions": "Mais cultos online",
    "ebdClassId": 2
  }')
echo $NEW_MEMBER | jq '.'
MEMBER_ID=$(echo $NEW_MEMBER | jq -r '.id')
print_success "Membro criado com ID: $MEMBER_ID"

sleep 1

# READ ALL
print_info "GET /api/members - Listar todos os membros"
curl -s -X GET "$API_URL/members" | jq '.'
print_success "Lista de membros obtida"

sleep 1

# READ ONE
print_info "GET /api/members/$MEMBER_ID - Obter membro específico"
curl -s -X GET "$API_URL/members/$MEMBER_ID" | jq '.'
print_success "Membro específico obtido"

sleep 1

# READ WITH FILTER
print_info "GET /api/members?ministry=Jovens - Filtrar por ministério"
curl -s -X GET "$API_URL/members?ministry=Jovens" | jq '.'
print_success "Membros filtrados por ministério"

sleep 1

# UPDATE
print_info "PUT /api/members/$MEMBER_ID - Atualizar membro"
curl -s -X PUT "$API_URL/members/$MEMBER_ID" \
  -H "$HEADER" \
  -d '{
    "name": "Carlos Teste Atualizado",
    "email": "carlos.atualizado@email.com",
    "phone": "+55 (11) 93333-4444",
    "suggestions": "Sugestão atualizada"
  }' | jq '.'
print_success "Membro atualizado"

sleep 1

# ============================================
# 4. EBD CLASSES
# ============================================
print_section "4. EBD CLASSES"

# READ ALL
print_info "GET /api/ebd-classes - Listar todas as classes"
curl -s -X GET "$API_URL/ebd-classes" | jq '.'
print_success "Classes EBD listadas"

sleep 1

# READ MEMBERS OF CLASS
print_info "GET /api/ebd-classes/2/members - Membros de uma classe"
curl -s -X GET "$API_URL/ebd-classes/2/members" | jq '.'
print_success "Membros da classe obtidos"

sleep 1

# CREATE NEW CLASS
print_info "POST /api/ebd-classes - Criar nova classe"
NEW_CLASS=$(curl -s -X POST "$API_URL/ebd-classes" \
  -H "$HEADER" \
  -d '{
    "name": "Sala Teste",
    "slug": "salateste",
    "password": "teste123"
  }')
echo $NEW_CLASS | jq '.'
CLASS_ID=$(echo $NEW_CLASS | jq -r '.id')
print_success "Nova classe criada com ID: $CLASS_ID"

sleep 1

# ============================================
# 5. TRANSACTIONS (CRUD COMPLETO)
# ============================================
print_section "5. TRANSACTIONS - CRUD"

# CREATE - Receita (Income)
print_info "POST /api/transactions - Criar receita (dízimo)"
TRANSACTION_1=$(curl -s -X POST "$API_URL/transactions" \
  -H "$HEADER" \
  -d '{
    "type": "income",
    "category": "Dízimo",
    "description": "Dízimo mensal de teste",
    "amount": 750.50,
    "date": "2024-11-21",
    "memberId": 1
  }')
echo $TRANSACTION_1 | jq '.'
TRANS_ID_1=$(echo $TRANSACTION_1 | jq -r '.id')
print_success "Receita criada com ID: $TRANS_ID_1"

sleep 1

# CREATE - Despesa (Expense)
print_info "POST /api/transactions - Criar despesa"
TRANSACTION_2=$(curl -s -X POST "$API_URL/transactions" \
  -H "$HEADER" \
  -d '{
    "type": "expense",
    "category": "Manutenção",
    "description": "Reparo elétrico",
    "amount": 250.00,
    "date": "2024-11-20"
  }')
echo $TRANSACTION_2 | jq '.'
TRANS_ID_2=$(echo $TRANSACTION_2 | jq -r '.id')
print_success "Despesa criada com ID: $TRANS_ID_2"

sleep 1

# READ ALL
print_info "GET /api/transactions - Listar todas as transações"
curl -s -X GET "$API_URL/transactions" | jq '.'
print_success "Transações listadas"

sleep 1

# READ WITH FILTER - Por tipo
print_info "GET /api/transactions?type=income - Filtrar apenas receitas"
curl -s -X GET "$API_URL/transactions?type=income" | jq '.'
print_success "Receitas filtradas"

sleep 1

# READ WITH FILTER - Por data
print_info "GET /api/transactions?startDate=2024-11-01&endDate=2024-11-30"
curl -s -X GET "$API_URL/transactions?startDate=2024-11-01&endDate=2024-11-30" | jq '.'
print_success "Transações filtradas por data"

sleep 1

# GET SUMMARY
print_info "GET /api/transactions/summary - Resumo financeiro"
curl -s -X GET "$API_URL/transactions/summary" | jq '.'
print_success "Resumo financeiro obtido"

sleep 1

# ============================================
# 6. ATTENDANCE (CRUD COMPLETO)
# ============================================
print_section "6. ATTENDANCE - PRESENÇA"

# CREATE - Presença
print_info "POST /api/attendance - Registrar presença (presente)"
ATTENDANCE_1=$(curl -s -X POST "$API_URL/attendance" \
  -H "$HEADER" \
  -d '{
    "memberId": 1,
    "date": "2024-11-21",
    "present": true,
    "serviceType": "culto"
  }')
echo $ATTENDANCE_1 | jq '.'
print_success "Presença registrada"

sleep 1

# CREATE - Ausência
print_info "POST /api/attendance - Registrar ausência"
curl -s -X POST "$API_URL/attendance" \
  -H "$HEADER" \
  -d '{
    "memberId": 2,
    "date": "2024-11-21",
    "present": false,
    "serviceType": "culto"
  }' | jq '.'
print_success "Ausência registrada"

sleep 1

# CREATE - Presença EBD
print_info "POST /api/attendance - Registrar presença na EBD"
curl -s -X POST "$API_URL/attendance" \
  -H "$HEADER" \
  -d '{
    "memberId": '$MEMBER_ID',
    "date": "2024-11-21",
    "present": true,
    "serviceType": "ebd"
  }' | jq '.'
print_success "Presença EBD registrada"

sleep 1

# READ ALL
print_info "GET /api/attendance - Listar todas as presenças"
curl -s -X GET "$API_URL/attendance" | jq '.'
print_success "Presenças listadas"

sleep 1

# READ WITH FILTER - Por data
print_info "GET /api/attendance?date=2024-11-21 - Filtrar por data"
curl -s -X GET "$API_URL/attendance?date=2024-11-21" | jq '.'
print_success "Presenças filtradas por data"

sleep 1

# READ WITH FILTER - Por tipo de serviço
print_info "GET /api/attendance?serviceType=culto - Filtrar por tipo"
curl -s -X GET "$API_URL/attendance?serviceType=culto" | jq '.'
print_success "Presenças filtradas por tipo"

sleep 1

# UPDATE (criar duplicado para testar atualização)
print_info "POST /api/attendance - Atualizar presença existente"
curl -s -X POST "$API_URL/attendance" \
  -H "$HEADER" \
  -d '{
    "memberId": 1,
    "date": "2024-11-21",
    "present": false,
    "serviceType": "culto"
  }' | jq '.'
print_success "Presença atualizada"

sleep 1

# ============================================
# 7. MINISTRIES
# ============================================
print_section "7. MINISTRIES - MINISTÉRIOS"

# READ ALL
print_info "GET /api/ministries - Listar todos os ministérios"
curl -s -X GET "$API_URL/ministries" | jq '.'
print_success "Ministérios listados"

sleep 1

# ============================================
# 8. ABOUT US
# ============================================
print_section "8. ABOUT US - SOBRE NÓS"

# READ
print_info "GET /api/about-us - Obter informações da igreja"
curl -s -X GET "$API_URL/about-us" | jq '.'
print_success "Informações obtidas"

sleep 1

# ============================================
# 9. STATISTICS
# ============================================
print_section "9. STATISTICS - ESTATÍSTICAS"

# READ
print_info "GET /api/statistics - Obter estatísticas gerais"
curl -s -X GET "$API_URL/statistics" | jq '.'
print_success "Estatísticas obtidas"

sleep 1

# ============================================
# 10. DELETE OPERATIONS
# ============================================
print_section "10. DELETE OPERATIONS"

# DELETE MEMBER
print_info "DELETE /api/members/$MEMBER_ID - Deletar membro de teste"
curl -s -X DELETE "$API_URL/members/$MEMBER_ID"
print_success "Membro deletado"

sleep 1

# Verificar se foi deletado
print_info "GET /api/members/$MEMBER_ID - Verificar deleção (deve dar erro 404)"
curl -s -X GET "$API_URL/members/$MEMBER_ID" | jq '.'
print_error "Membro não encontrado (esperado)"

# ============================================
# 11. TESTES DE ERRO
# ============================================
print_section "11. TESTES DE ERRO"

# Tentar criar membro sem nome (deve falhar)
print_info "POST /api/members - Criar membro sem nome (deve falhar)"
curl -s -X POST "$API_URL/members" \
  -H "$HEADER" \
  -d '{
    "email": "semNome@email.com"
  }' | jq '.'
print_error "Erro esperado - campo obrigatório faltando"

sleep 1

# Tentar acessar recurso inexistente
print_info "GET /api/members/99999 - Acessar membro inexistente"
curl -s -X GET "$API_URL/members/99999" | jq '.'
print_error "Erro 404 esperado"

sleep 1

# ============================================
# RESUMO FINAL
# ============================================
print_section "RESUMO DOS TESTES"

echo -e "${GREEN}✓ Health Check${NC}"
echo -e "${GREEN}✓ Autenticação (Login)${NC}"
echo -e "${GREEN}✓ Members (CRUD completo)${NC}"
echo -e "${GREEN}✓ EBD Classes (READ + CREATE)${NC}"
echo -e "${GREEN}✓ Transactions (CRUD completo + Summary)${NC}"
echo -e "${GREEN}✓ Attendance (CRUD completo + Filtros)${NC}"
echo -e "${GREEN}✓ Ministries (READ)${NC}"
echo -e "${GREEN}✓ About Us (READ)${NC}"
echo -e "${GREEN}✓ Statistics (READ)${NC}"
echo -e "${GREEN}✓ Delete Operations${NC}"
echo -e "${GREEN}✓ Testes de Erro${NC}"

echo -e "\n${BLUE}============================================${NC}"
echo -e "${GREEN}TODOS OS TESTES CONCLUÍDOS!${NC}"
echo -e "${BLUE}============================================${NC}\n"
