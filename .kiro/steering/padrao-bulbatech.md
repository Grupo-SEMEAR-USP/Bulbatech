---
inclusion: always
---
# Regras Obrigatórias — Projeto Bulbatech (ROS 2 Jazzy)

## Perfil do Desenvolvedor e Estilo de Código
- Escreva código Python simples, linear e legível para nível iniciante/intermediário.
- Proibido: herança múltipla, decorators customizados, metaclasses, lambdas complexas, list comprehensions aninhadas, operadores ternários encadeados, MultiThreadedExecutor, LifecycleNode e async/await.
- Use apenas rclpy.node.Node, create_publisher, create_subscription, create_timer, declare_parameter e get_logger().
- Limite cada método ou callback a no máximo 30 linhas; quebre lógicas maiores em métodos auxiliares privados (_nome_descritivo).
- Exponha todos os ganhos, limiares e timeouts via declare_parameter no __init__.

## Estilo, Linter e Comentários
- Respeite estritamente flake8 (máximo 99 caracteres por linha, sem imports não utilizados) e pep257 (docstring simples de uma linha no módulo, classe e métodos públicos).
- Não adicione comentários narrativos óbvios (ex.: # Cria o publisher). Comente apenas fórmulas físicas ou regras de segurança.

## Modo de Trabalho
- Nunca altere múltiplos arquivos ou execute várias tarefas de uma vez. Faça uma tarefa por turno e aguarde validação.
