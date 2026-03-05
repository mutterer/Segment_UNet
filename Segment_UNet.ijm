if (nImages<1) exit("Requires an image"); 
imagePath=getInfo("image.directory")+getInfo("image.filename");
id=getImageID;
t=getTitle();
showProgress(0.5);
output=call('ij.Prefs.get','dl.output',getDir('temp')+'out.png');
checkpoint=call('ij.Prefs.get','dl.checkpoint','not set');
envname=call('ij.Prefs.get','dl.envname','');

if (!checkpoint.endsWith('.pt')) exit ('No weights file selected');

platform = getInfo("os.name");
if (platform=="Linux") {
   exec(getDir('plugins')+"Angers/scripts/run_process_single_image.sh",
   "--input",imagePath,"--output",output, "--checkpoint",checkpoint,"--env-name",envname);
} else {
   // windows?
   exec("wsl","bash","'"+fixPath(getDirectory("plugins")+"Angers/scripts/run_process_single_image.sh"+"'"),
   "--input",fixPath(imagePath),"--output",fixPath(output), "--checkpoint",fixPath(checkpoint),"--env-name",envname);
}

open(output);
rename("segmented_"+t);

function fixPath(s) {
   s=s.replace("\\","/");
   s=s.replace("C:","/mnt/c");
   return s;
}
