import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
s=importlib.util.spec_from_file_location('album',Path(__file__).parents[1]/'scripts'/'album.py')
m=importlib.util.module_from_spec(s); s.loader.exec_module(m)

class Tests(unittest.TestCase):
    def test_copy_restore_and_safety(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); src=root/'src'; src.mkdir()
            (src/'a.jpg').write_bytes(b'synthetic a'); (src/'b.jpg').write_bytes(b'synthetic b')
            plan=root/'plan.json'; plan.write_text(json.dumps({'groups':[{'id':'1','keeper':'b.jpg','files':['a.jpg','b.jpg'],'reason':'test'}]}))
            out=root/'out'; self.assertEqual(m.apply(src,plan,out),2)
            self.assertEqual((src/'a.jpg').read_bytes(),b'synthetic a')
            restored=m.restore(out,'a.jpg',root/'restored')
            self.assertEqual(Path(restored).read_bytes(),b'synthetic a')
            with self.assertRaises(ValueError): m.apply(src,plan,out)
            with self.assertRaises(ValueError): m.inside(root,'../escape')
            (out/'memories'/'a.jpg').write_bytes(b'changed')
            with self.assertRaises(ValueError): m.restore(out,'a.jpg',root/'again')

if __name__=='__main__': unittest.main()
