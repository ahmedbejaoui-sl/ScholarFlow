from app.services.assignment_service import calculer_affectations


def test_chacun_obtient_son_premier_choix_sans_conflit():
    voeux = {1: [10, 11], 2: [11, 10]}
    assert calculer_affectations(voeux, [1, 2]) == {1: 10, 2: 11}


def test_conflit_le_premier_de_l_ordre_gagne():
    voeux = {1: [10, 11], 2: [10, 11]}
    # L'étudiant 1 a validé en premier : il obtient le sujet 10, l'étudiant 2 son 2e choix
    assert calculer_affectations(voeux, [1, 2]) == {1: 10, 2: 11}


def test_un_sujet_n_est_attribue_qu_a_un_seul_etudiant():
    voeux = {1: [10], 2: [10], 3: [10]}
    resultat = calculer_affectations(voeux, [1, 2, 3])
    assert list(resultat.values()) == [10]
    assert resultat == {1: 10}


def test_un_premier_choix_passe_avant_un_deuxieme_choix():
    # L'étudiant 1 passe avant 2 dans l'ordre, mais le sujet 6 est le 2e choix de 1
    # et le 1er choix de 2 : c'est 2 qui l'obtient.
    voeux = {3: [9], 1: [9, 6], 2: [6]}
    assert calculer_affectations(voeux, [3, 1, 2]) == {3: 9, 2: 6}


def test_etudiant_sans_voeux_n_est_pas_affecte():
    assert calculer_affectations({1: []}, [1]) == {}


def test_aucun_etudiant():
    assert calculer_affectations({}, []) == {}