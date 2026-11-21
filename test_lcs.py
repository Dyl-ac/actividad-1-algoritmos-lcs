import itertools
import random
import unittest
from lcs import VERSIONES, es_subsecuencia, lcs_hirschberg, lcs_tabular


class PruebasLCS(unittest.TestCase):
    def comprobar(self, x, y, longitud=None):
        esperado = len(lcs_tabular(x, y)) if longitud is None else longitud
        for nombre, funcion in VERSIONES.items():
            with self.subTest(version=nombre, x=x, y=y):
                salida = funcion(x, y)
                self.assertTrue(es_subsecuencia(salida, x))
                self.assertTrue(es_subsecuencia(salida, y))
                self.assertEqual(len(salida), esperado)

    def test_conocidos(self):
        for x, y, longitud in [('', '', 0), ('', 'ABC', 0), ('ABC', '', 0),
                               ('AAAA', 'AAAA', 4), ('ABC', 'DEF', 0),
                               ('ABCBDAB', 'BDCABA', 4), ('á🙂b', '🙂áb', 2),
                               ('A', 'BAA', 1), ('BAA', 'A', 1)]:
            self.comprobar(x, y, longitud)

    def test_exhaustivo_binario(self):
        cadenas = [''.join(p) for n in range(5) for p in itertools.product('AB', repeat=n)]
        for x in cadenas:
            for y in cadenas:
                self.comprobar(x, y)

    def test_casos_aleatorios(self):
        rng = random.Random(12345)
        for _ in range(100):
            x = ''.join(rng.choices('ACGT', k=rng.randrange(13)))
            y = ''.join(rng.choices('ACGT', k=rng.randrange(13)))
            self.comprobar(x, y)

    def test_rangos_desiguales_y_grandes(self):
        for x, y in [('AB' * 500, 'BA' * 300), ('ABC' * 500, 'CAB'), ('X' * 1000, 'Y' * 1000)]:
            b, c = lcs_hirschberg(x, y), lcs_tabular(x, y)
            self.assertEqual(len(b), len(c))
            self.assertTrue(es_subsecuencia(b, x) and es_subsecuencia(b, y))


if __name__ == '__main__':
    unittest.main()
