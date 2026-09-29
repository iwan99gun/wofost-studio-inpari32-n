"""Lengkapi pustaka tulis-tangan di buat_naskah.py: DOI terverifikasi Crossref (29 Sep 2026) + nama jurnal lengkap
(konsisten dengan entri pustaka_terverifikasi.json yang memakai nama lengkap)."""
from pathlib import Path

F = Path(__file__).resolve().parent / "buat_naskah.py"
s = F.read_text(encoding="utf-8")
R = [
    ('Eur. J. Agron. 101, 10–19. "', 'European Journal of Agronomy 101, 10–19. "'),
    ('"Ambio 31, 132–140.", False)', '"Ambio 31, 132–140. https://doi.org/10.1579/0044-7447-31.2.132", False)'),
    ('Agric. Syst. 168, 154–167. "', 'Agricultural Systems 168, 154–167. "'),
    ('Agron. J. 95, 913–923. "', 'Agronomy Journal 95, 913–923. "'),
    ('"Agron. J. 95, 924–935. https', '"Agronomy Journal 95, 924–935. https'),
    ('emcee: the MCMC hammer. Publ. Astron. Soc. Pac. 125, 306–312.", False)',
     'emcee: the MCMC hammer. Publications of the Astronomical Society of the Pacific 125, 306–312. '
     'https://doi.org/10.1086/670067", False)'),
    ('"J. Exp. Bot. 53, 789–799.", False)',
     '"Journal of Experimental Botany 53, 789–799. https://doi.org/10.1093/jexbot/53.370.789", False)'),
    ('J. Open Source Softw. 2(9), 97.", False)',
     'Journal of Open Source Software 2(9), 97. https://doi.org/10.21105/joss.00097", False)'),
    ('("Hersbach, H., et al., 2020. The ERA5 global reanalysis. Q. J. R. Meteorol. Soc. 146, 1999–2049.", False)',
     '("Hersbach, H., Bell, B., Berrisford, P., et al., 2020. The ERA5 global reanalysis. Quarterly Journal of the Royal '
     'Meteorological Society 146, 1999–2049. https://doi.org/10.1002/qj.3803", False)'),
    ('J. Agron. Indonesia 49(3), 242–250.', 'Jurnal Agronomi Indonesia 49(3), 242–250.'),
    ('"and practices for crop N management. Eur. J. Agron. 28, 614–624.", False)',
     '"and practices for crop N management. European Journal of Agronomy 28, 614–624. '
     'https://doi.org/10.1016/j.eja.2008.01.005", False)'),
    ('Comput. Phys. Commun. 145, 280–297.", False)',
     'Computer Physics Communications 145, 280–297. https://doi.org/10.1016/s0010-4655(02)00280-1", False)'),
    ('application to rice. Eur. J. Agron. 32, 255–271.', 'application to rice. European Journal of Agronomy 32, 255–271.'),
    ('"Math. Comput. Simul. 55, 271–280.", False)',
     '"Mathematics and Computers in Simulation 55, 271–280. https://doi.org/10.1016/s0378-4754(00)00270-6", False)'),
    ('"IOP Conf. Ser.: Earth Environ. Sci. 1165, 012026.', '"IOP Conference Series: Earth and Environmental Science 1165, 012026.'),
    ('"Soil Use Manage. 5, 16–24.", False)',
     '"Soil Use and Management 5, 16–24. https://doi.org/10.1111/j.1475-2743.1989.tb00755.x", False)'),
    ('"local to global relevance—a review. Field Crops Res. 143, 4–17.", False)',
     '"local to global relevance—a review. Field Crops Research 143, 4–17. '
     'https://doi.org/10.1016/j.fcr.2012.09.009", False)'),
]
for a, b in R:
    assert s.count(a) == 1, (s.count(a), a)
    s = s.replace(a, b)
F.write_text(s, encoding="utf-8")
print("ok", len(R))
