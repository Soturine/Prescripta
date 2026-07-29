# Política de segurança

Não abra issue pública com credenciais, dados de pacientes ou detalhes exploráveis.

Reporte vulnerabilidades pelo recurso **Security advisories** do repositório no GitHub. Inclua a
versão, impacto, pré-condições e uma reprodução sem dados reais. O mantenedor fará triagem inicial
em até 5 dias úteis e coordenará correção e divulgação. O Prescripta v0.8.6 é demonstrativo e não
possui validação clínica formal para uso assistencial real.

Segredos devem vir do ambiente ou de secret manager; nunca inclua `.env`, token, API key, CPF,
CNS, telefone, endereço ou e-mail de paciente em um relato ou fixture.
