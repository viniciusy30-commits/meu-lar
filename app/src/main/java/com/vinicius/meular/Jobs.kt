package com.vinicius.meular

/**
 * Etapa 141: profissões do jogo. Cada uma tem nível (1 começo … 4 topo), salário por turno, vantagem
 * e um local de trabalho único na cidade (o prédio só existe uma vez no mapa).
 * Os minigames serão definidos depois; aqui ficam os dados e o lugar de cada profissão.
 */
object Jobs {
    class Job(val id: String, val name: String, val level: Int, val place: String, val sign: String, val salary: Int, val perk: String, val requires: String)

    val ALL = listOf(
        // nível 1 — começo (sem estudo)
        Job("diarista", "Diarista", 1, "Brilho Limpeza", "LIMPEZA BRILHO", 120, "Faxina grátis na sua casa uma vez por semana", ""),
        Job("lixeiro", "Lixeiro", 1, "Central de Coleta", "CENTRAL DE COLETA", 130, "Bônus de pontualidade (turno começa cedo)", ""),
        Job("atendente", "Atendente", 1, "Lanchonete do Zé", "LANCHONETE", 110, "Lanche grátis em todo turno", ""),
        Job("entregador", "Entregador", 1, "Expresso Já", "CENTRAL DE ENTREGAS", 140, "Moto da empresa durante o turno", ""),
        Job("frentista", "Frentista", 1, "Posto Rota Sul", "POSTO", 125, "Desconto no combustível", ""),
        Job("repositor", "Repositor", 1, "SuperBom", "SUPERMERCADO", 115, "Desconto nas compras do mercado", ""),
        // nível 2 — intermediário (curso técnico)
        Job("professor", "Professor(a)", 2, "Escola Primavera", "ESCOLA", 260, "Férias pagas e prestígio no bairro", "Licenciatura"),
        Job("secretario", "Secretário(a)", 2, "Escritório Central", "ESCRITÓRIOS", 240, "Horário fixo: noites livres", "Curso técnico"),
        Job("policial", "Policial", 2, "Delegacia", "POLÍCIA", 300, "Viatura e acesso à delegacia", "Academia de polícia"),
        Job("bombeiro", "Bombeiro(a)", 2, "Quartel dos Bombeiros", "BOMBEIROS", 290, "Respeito da cidade e treino físico", "Curso de bombeiro"),
        Job("mecanico", "Mecânico(a)", 2, "Oficina do Toninho", "OFICINA", 250, "Conserto do seu carro de graça", "Curso técnico"),
        Job("enfermeiro", "Enfermeiro(a)", 2, "Clínica Aurora", "CLÍNICA", 280, "Atendimento de saúde grátis", "Técnico em enfermagem"),
        // nível 3 — alto (faculdade)
        Job("medico", "Médico(a)", 3, "Hospital Santa Clara", "HOSPITAL", 620, "Plano de saúde completo", "Medicina"),
        Job("advogado", "Advogado(a)", 3, "Almeida & Prado", "ADVOCACIA", 560, "Contratos e multas resolvidos", "Direito"),
        Job("juiz", "Juiz(a)", 3, "Fórum da Comarca", "FÓRUM", 780, "Motorista particular", "Direito + concurso"),
        Job("engenheiro", "Engenheiro(a)", 3, "Pilar Construtora", "CONSTRUTORA", 540, "Reforma da casa com desconto", "Engenharia"),
        Job("programador", "Programador(a)", 3, "Nova Tech", "TECNOLOGIA", 580, "Pode trabalhar de casa", "Computação"),
        // nível 4 — topo
        Job("empresario", "Empresário(a)", 4, "Grupo Atlas", "SEDE", 1500, "Lucro da empresa e carro de luxo", "Experiência de nível 3"),
        Job("prefeito", "Prefeito(a)", 4, "Prefeitura", "PREFEITURA", 1200, "Decide obras da cidade", "Eleição"))

    fun byId(id: String) = ALL.firstOrNull { it.id == id }

    /** Turnos trabalhados necessários para liberar cada nível (nível 1 é livre). */
    val NEED = intArrayOf(0, 0, 5, 15, 35)
    val LEVEL_NAME = arrayOf("", "Começo", "Técnico", "Faculdade", "Topo")
    fun unlocked(level: Int, shifts: Int) = shifts >= NEED[level.coerceIn(1, 4)]
    /** Intervalo mínimo entre dois pontos batidos (um turno). */
    const val SHIFT_MS = 90_000L
}
