"""Uji asap: pustaka analisis terpasang dan cocok dengan solusi analitik sederhana.

Kantilever L = 3 m, beban ujung P = 10 kN, E = 25 GPa, penampang 300x500 mm.
Lendutan ujung analitik: P L^3 / (3 E I).
"""
import pytest

L, P, E = 3.0, 10.0, 25e6          # m, kN, kPa
b, h = 0.3, 0.5
I = b * h**3 / 12                   # m^4
A = b * h
DELTA = P * L**3 / (3 * E * I)      # m


def test_pynite_kantilever():
    from Pynite import FEModel3D
    m = FEModel3D()
    m.add_node('A', 0, 0, 0)
    m.add_node('B', L, 0, 0)
    m.add_material('beton', E, E / 2.4, 0.2, 24)
    m.add_section('kolom', A, I, I, 2 * I)
    m.add_member('M1', 'A', 'B', 'beton', 'kolom')
    m.def_support('A', True, True, True, True, True, True)
    m.add_node_load('B', 'FY', -P)
    m.analyze_linear()
    assert abs(m.nodes['B'].DY['Combo 1']) == pytest.approx(DELTA, rel=1e-6)


def test_openseespy_kantilever():
    import openseespy.opensees as ops
    ops.wipe()
    ops.model('basic', '-ndm', 2, '-ndf', 3)
    ops.node(1, 0, 0)
    ops.node(2, L, 0)
    ops.fix(1, 1, 1, 1)
    ops.geomTransf('Linear', 1)
    ops.element('elasticBeamColumn', 1, 1, 2, A, E, I, 1)
    ops.timeSeries('Linear', 1)
    ops.pattern('Plain', 1, 1)
    ops.load(2, 0, -P, 0)
    ops.system('BandGen'); ops.numberer('Plain'); ops.constraints('Plain')
    ops.integrator('LoadControl', 1.0); ops.algorithm('Linear'); ops.analysis('Static')
    assert ops.analyze(1) == 0
    assert abs(ops.nodeDisp(2, 2)) == pytest.approx(DELTA, rel=1e-6)


def test_ifcopenshell_buat_kolom():
    import ifcopenshell.api
    f = ifcopenshell.api.run('project.create_file', version='IFC4')
    ifcopenshell.api.run('root.create_entity', f, ifc_class='IfcProject', name='uji')
    ifcopenshell.api.run('root.create_entity', f, ifc_class='IfcColumn', name='K1')
    assert len(f.by_type('IfcColumn')) == 1
