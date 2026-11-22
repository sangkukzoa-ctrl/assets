#!/usr/bin/env python3
"""Run EXACT production C&B rendered-quads oracle against the shipped Scena API.

The upstream 1.20.1/1.21.1 C&B builds use IBlockModelData.getData(IModelDataKey)
and ModModelProperties.KNOWN_LAYER_MODEL_PROPERTY. Exercise the production
reflection path and actual BakedModel.getQuads(side) calls on Java17 and 21.
Minimal model-data stand-ins use the *official published interface signatures*.
This is an executable production-method regression, NOT a Minecraft game PASS.
"""
from pathlib import Path
import subprocess
import tempfile

source = Path(
    "rgb-blocks-compat/recovered/fabric/com/rgbblocks/client/cnb/RGBCnbMeshIntegrity.java"
).read_text(encoding="utf-8")

def production_method(signature):
    start = source.index(signature)
    open_at = source.index("{", start)
    depth = 0
    for i in range(open_at, len(source)):
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
            if depth == 0:
                return source[start:i + 1]
    raise AssertionError("Unbalanced production C&B method " + signature)

actual = "\n".join((
    production_method("private static boolean hasActualRenderedQuads("),
    production_method("private static Method findZeroArg("),
))
for token in (
    'findZeroArg(tile.getClass(),"getBlockModelData")',
    'Class.forName("mod.chiselsandbits.registrars.ModModelProperties")',
    '"KNOWN_LAYER_MODEL_PROPERTY"',
    'Class.forName("com.communi.suggestu.scena.core.client.models.data.IBlockModelData")',
    'Class.forName("com.communi.suggestu.scena.core.client.models.data.IModelDataKey")',
    'modelData.getMethod("getData",keyType).invoke(data,key)',
    'baked.getQuads(null,face,random).isEmpty()',
    'baked.getQuads(null,null,random).isEmpty()',
):
    assert token in actual, ("C&B native model oracle API regressed", token)

scena_key = """package com.communi.suggestu.scena.core.client.models.data;
public interface IModelDataKey<T> {}
"""
scena_data = """package com.communi.suggestu.scena.core.client.models.data;
public interface IBlockModelData {
    boolean hasProperty(IModelDataKey<?> prop);
    <T> T getData(IModelDataKey<T> prop);
}
"""
cnb_properties = """package mod.chiselsandbits.registrars;
import com.communi.suggestu.scena.core.client.models.data.IModelDataKey;
public final class ModModelProperties {
    public static IModelDataKey<Object> KNOWN_LAYER_MODEL_PROPERTY =
        new IModelDataKey<Object>() {};
}
"""
java = r'''import java.util.*;
import java.lang.reflect.Method;
import com.communi.suggestu.scena.core.client.models.data.IBlockModelData;
import com.communi.suggestu.scena.core.client.models.data.IModelDataKey;
import mod.chiselsandbits.registrars.ModModelProperties;

public final class RGBMeshOracleModelDataRegression {
    static class BlockEntity {
        private final Object data;
        BlockEntity(Object data){this.data=data;}
        public Object getBlockModelData(){return data;}
    }
    // A package-private implementation of a PUBLIC Scena interface is a
    // deliberate reflection boundary case, matching the real mod loader.
    static final class MockScenaData implements IBlockModelData {
        final Map<IModelDataKey<?>,Object> values=new HashMap<>();
        MockScenaData(Object layers){
            if(layers!=null)values.put(ModModelProperties.KNOWN_LAYER_MODEL_PROPERTY,layers);
        }
        public boolean hasProperty(IModelDataKey<?> key){return values.containsKey(key);}
        @SuppressWarnings("unchecked")
        public <T>T getData(IModelDataKey<T> key){return (T)values.get(key);}
    }
    enum Direction {DOWN,UP,NORTH,SOUTH,WEST,EAST}
    static class RandomSource {
        static RandomSource create(){return new RandomSource();}
    }
    interface BakedModel {
        List<Integer> getQuads(Object state,Direction side,RandomSource random);
    }
    static final class Model implements BakedModel {
        final Direction visibleSide;
        final boolean generic;
        int queried;
        Model(Direction side,boolean generic){
            this.visibleSide=side;
            this.generic=generic;
        }
        public List<Integer> getQuads(Object state,Direction side,RandomSource rand){
            queried++;
            if(side==visibleSide && !generic && side!=null)return List.of(1,2);
            if(side==null && generic)return List.of(3);
            return List.of();
        }
    }

    /* EXACT_PRODUCTION_METHODS */

    static void check(boolean value,String message){
        if(!value)throw new AssertionError(message);
    }
    static boolean test(Object data)throws Exception{
        return hasActualRenderedQuads(new BlockEntity(data));
    }
    public static void main(String[] args)throws Exception {
        check(!test(null),"Null Scena model data returned fake quads");
        check(!test(new MockScenaData(null)),"Unset C&B KNOWN_LAYER key returned true");
        check(!test(new MockScenaData("not_a_map")),
            "Unknown Scena model-data shape was mistaken for model geometry");
        check(!test(new MockScenaData(Map.of())),
            "Empty loaded render-layer map returned phantom geometry");
        check(!test(new MockScenaData(Map.of("layer","not_a_model"))),
            "Non-BakedModel renderer value returned phantom geometry");

        Model empty=new Model(null,false);
        check(!test(new MockScenaData(Map.of("solid",empty))),
            "Empty baked model was mistaken for real C&B quads");
        check(empty.queried==7,
            "C&B oracle did not inspect 6 directions plus unculled quads");

        Model singleFace=new Model(Direction.WEST,false);
        check(test(new MockScenaData(Map.of("solid",singleFace))),
            "Real face-culling quads were not detected from C&B model data");
        check(singleFace.queried>0 && singleFace.queried<=6,
            "RGB mesh oracle did not inspect the correct side model quads");

        Model unculled=new Model(null,true);
        check(test(new MockScenaData(Map.of("translucent",unculled))),
            "Unculled colored glass C&B quads were not detected");
        check(unculled.queried==7,
            "Unculled geometry should be checked after six culled sides");

        Model missing=new Model(null,false);
        Model available=new Model(Direction.NORTH,false);
        Map<String,Object> mixed=new LinkedHashMap<>();
        mixed.put("invalid",missing);
        mixed.put("solid",available);
        check(test(new MockScenaData(mixed)),
            "A second valid C&B render layer was ignored after empty first layer");

        boolean missingGetterIsError=false;
        try{hasActualRenderedQuads(new ObjectTile());}
        catch(NoSuchMethodException expected){missingGetterIsError=true;}
        check(missingGetterIsError,
            "A changed native C&B method signature must fail visibly, not fake PASS");

        System.out.println("RGB_PORT_CNB_SCENA_RENDERED_QUADS_JAVAC_PASS"+
          " real_scena_getData_signature=true"+
          " empty_map_false=true non_model_false=true"+
          " six_sides_and_unculled=true colored_glass_unculled=true"+
          " multiple_render_layers=true nonpublic_model_data=true"+
          " missing_native_getter_reported=true");
    }
    static final class ObjectTile extends BlockEntity {
        ObjectTile(){super(null);}
        // Note: Java inheritance is real. This subclass still has a getter
        // and so should not exercise missing API; use a guard below instead.
    }
}
'''.replace("/* EXACT_PRODUCTION_METHODS */",actual)
# An ObjectTile subclass inherits a valid getBlockModelData(). Test an
# intentionally broken non-public implementation API without weakening the
# typed method body or constructing an unsupported Minecraft BlockEntity.
java=java.replace(
    '''        boolean missingGetterIsError=false;
        try{hasActualRenderedQuads(new ObjectTile());}
        catch(NoSuchMethodException expected){missingGetterIsError=true;}
        check(missingGetterIsError,
            "A changed native C&B method signature must fail visibly, not fake PASS");
''',
    '''        // Inspect the real findZeroArg lookup against a class that lacks
        // a C&B model-data callback entirely. Errors must remain visible.
        boolean missingGetterIsError=false;
        try{findZeroArg(MissingNativeApi.class,"getBlockModelData");}
        catch(NoSuchMethodException expected){missingGetterIsError=true;}
        check(missingGetterIsError,
            "A changed native C&B method signature must fail visibly, not fake PASS");
'''
).replace(
    '''    static final class ObjectTile extends BlockEntity {
        ObjectTile(){super(null);}
        // Note: Java inheritance is real. This subclass still has a getter
        // and so should not exercise missing API; use a guard below instead.
    }
''',
    '''    static final class MissingNativeApi {}
''')
with tempfile.TemporaryDirectory(prefix="rgb-cnb-scena-quads-") as d:
    root=Path(d)
    files={
        "RGBMeshOracleModelDataRegression.java":java,
        "com/communi/suggestu/scena/core/client/models/data/IModelDataKey.java":scena_key,
        "com/communi/suggestu/scena/core/client/models/data/IBlockModelData.java":scena_data,
        "mod/chiselsandbits/registrars/ModModelProperties.java":cnb_properties,
    }
    sources=[]
    for name,body in files.items():
        path=root/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(body,encoding="utf-8")
        sources.append(str(path))
    for version in ("17","21"):
        out=root/("java"+version)
        out.mkdir()
        compilation=subprocess.run(
            ["javac","--release",version,"-encoding","UTF-8","-d",str(out)]+sources,
            capture_output=True,text=True,timeout=45)
        if compilation.returncode:
            raise RuntimeError("C&B actual Scena model API Java "+version+
                " compile:\n"+compilation.stdout[-3000:]+compilation.stderr[-8000:])
        execution=subprocess.run(
            ["java","-cp",str(out),"RGBMeshOracleModelDataRegression"],
            capture_output=True,text=True,timeout=25)
        if execution.returncode:
            raise RuntimeError("C&B actual model oracle Java "+version+
                " failed:\n"+execution.stdout[-3000:]+execution.stderr[-8000:])
        assert "RGB_PORT_CNB_SCENA_RENDERED_QUADS_JAVAC_PASS" in execution.stdout
        print("JAVA "+version+" "+execution.stdout.strip(),flush=True)
