# 📂 Shard: Infraestructura Cloud y CI/CD (v1.0)
**Última Actualización:** 2025-12-24  
**Fuentes:** Soul Packages [20251223_234652, 20251224_000601, 20251224_000913]  
**Contexto:** Arquitectura Hexagonal aplicada a AWS con FastAPI

---

## 🏗️ Arquitectura de Backend

### Estructura Principal
- **Framework:** FastAPI con Python 3.12+
- **Patrón:** Arquitectura Hexagonal (Ports & Adapters)
- **Separación de capas:** Dominio, Aplicación, Infraestructura
- **Type Hints:** Estrictos, compatibles con mypy --strict
- **Clean Code:** Principios SOLID aplicados

### Seguridad y Autenticación
- **Guardian Middleware:** Filtrado de mensajes con bypass mediante `RAG_API_KEY`
- **Comparación segura:** Uso de `secrets.compare_digest` para evitar timing attacks
- **OAuth2 + JWT:** Tokens de acceso y refresh tokens
- **Secrets Manager:** Credenciales almacenadas en AWS Secrets Manager
- **Inyección hexagonal:** API Key inyectada desde settings para testabilidad

---

## ☁️ AWS Fargate & Networking

### Despliegue de Contenedores
- **Plataforma:** ECS Fargate (serverless containers)
- **Registro:** ECR (Elastic Container Registry) para imágenes Docker
- **Networking:** VPC privada con subnets públicas/privadas
- **Load Balancer:** Application Load Balancer (ALB) para distribución de tráfico
- **Security Groups:** Configuración de tráfico desde ALB a Fargate y de Fargate a RDS

### Persistencia y Escalabilidad
- **Bases de datos:** RDS (PostgreSQL) y DocumentDB (MongoDB)
- **Integración RAG:** Gemini para consultas complejas
- **Integración Guardian:** Qwen para validación de código
- **Auto Scaling:** Escalado horizontal basado en métricas de CloudWatch

---

## 🚀 Pipeline CI/CD Inmutable

### Flujo Completo
1. **Trigger:** Git push a rama principal en GitHub
2. **Orquestación:** CodePipeline detecta cambio y desencadena flujo
3. **Build:** CodeBuild compila código y ejecuta tests
4. **Registro:** Imagen Docker subida a ECR con escaneo de vulnerabilidades
5. **Deploy:** CodeDeploy despliega en ECS Fargate
6. **Verificación:** Health checks y monitoreo con CloudWatch

### Configuración de CodeBuild (buildspec.yml)
```yaml
version: 0.2.0

phases:
  install:
    runtime-versions:
      python: 3.12
  build:
    commands:
      - pip install fastapi uvicorn pytest
      - pytest tests/  # Tests ANTES del build
      - docker build -t app:latest .
  post_build:
    commands:
      - docker tag app:latest $ECR_REPO:$CODEBUILD_RESOLVED_SOURCE_VERSION
      - docker push $ECR_REPO:$CODEBUILD_RESOLVED_SOURCE_VERSION
```

### Estrategia de Despliegue
- **Método:** Blue/Green Deployment con AppSpec
- **Ventajas:** Zero downtime, rollback instantáneo
- **Configuración:** Dos entornos (azul/verde) con tráfico redirigido gradualmente
- **Validación:** Tests de integración en entorno verde antes de switch completo

### Calidad y Testing
- **Unit Tests:** Pytest con cobertura mínima 80%
- **Integration Tests:** Validación de endpoints con AsyncMock
- **Type Checking:** mypy --strict en pipeline
- **Linting:** Ruff para estilo de código

### Rollback Automático
- **Monitoreo:** CloudWatch Alarms en métricas críticas
- **Triggers:** Error rate > 5%, latencia > 2s, health check failures
- **Acción:** CodeDeploy revierte automáticamente a versión anterior (entorno azul)
- **Notificaciones:** SNS para alertas al equipo

---

## 🔑 Mejores Prácticas Confirmadas

### Secrets Management
- **Nunca hardcodear:** API Keys, DB credentials, JWT secrets
- **Secrets Manager:** Rotación automática de credenciales
- **IAM Roles:** Permisos mínimos necesarios (Principle of Least Privilege)
- **Inyección en runtime:** Variables de entorno desde Secrets Manager a Fargate

### Arquitectura Hexagonal en AWS
- **Ports:** Interfaces abstractas (ej. `ISecretsRepository`)
- **Adapters:** Implementaciones concretas (ej. `AWSSecretsAdapter`)
- **Beneficio:** Cambiar de Secrets Manager a HashiCorp Vault sin tocar dominio
- **Testing:** Mock de adapters para tests unitarios rápidos

### Docker en ECS Fargate
- **Multi-stage builds:** Reducir tamaño de imagen final
- **Health checks:** Endpoint `/health` para ECS Task Definition
- **Logs:** CloudWatch Logs con structured logging (JSON)
- **Resources:** CPU/Memory limits definidos en Task Definition

---

## 📊 Decisiones Técnicas Clave

### Por qué Fargate sobre EC2
- ✅ Sin gestión de servidores
- ✅ Escalado automático sin configuración de ASG
- ✅ Pago por uso (no por instancias reservadas)
- ✅ Integración nativa con ALB y CloudWatch

### Por qué Blue/Green sobre Rolling
- ✅ Rollback instantáneo (cambio de DNS/ALB target)
- ✅ Testing completo en entorno verde antes de producción
- ✅ Zero downtime garantizado
- ✅ Fácil validación de smoke tests

### Por qué secrets.compare_digest
- ✅ Previene timing attacks en comparación de API Keys
- ✅ Estándar de seguridad en Python
- ✅ Recomendación de OWASP para comparación de secretos

---

## 🧪 Comandos de Validación

### Verificar Secrets en Fargate
```bash
# Obtener logs del contenedor
aws logs tail /ecs/app-task --follow

# Verificar que RAG_API_KEY se inyectó correctamente
aws ecs describe-task-definition --task-definition app-task \
  | jq '.taskDefinition.containerDefinitions[0].secrets'
```

### Verificar Health de CodeDeploy
```bash
# Estado del deployment
aws deploy get-deployment --deployment-id <ID>

# Logs de CodeBuild
aws codebuild batch-get-builds --ids <BUILD_ID>
```

### Rollback Manual
```bash
# Revertir a deployment anterior
aws deploy stop-deployment --deployment-id <ID> --auto-rollback-enabled
```

---

## 🎯 Tags de Conocimiento
`#aws` `#ecs` `#fargate` `#codepipeline` `#codebuild` `#fastapi` `#hexagonal-architecture` `#cicd` `#devops` `#secrets-manager` `#blue-green-deployment` `#docker` `#ecr`
