// Action Bar description file :DL_Drop
run("Action Bar","/plugins/ActionBar/DL_Drop.ijm");
exit();

<line>
<text> Drag and Drop image to segment
</line>
<line>
<button>
label=Preferences...
arg=<macro>
output=call('ij.Prefs.get','dl.output',getDir('temp')+'out.png');
checkpoint=call('ij.Prefs.get','dl.checkpoint','not set');
envname=call('ij.Prefs.get','dl.envname','seg-stomate-cpu');

Dialog.create("Preferences");
Dialog.addString("env name", envname,50);
Dialog.addFile("model", checkpoint, 50);
Dialog.show();
envname=Dialog.getString();
checkpoint=Dialog.getString();
call('ij.Prefs.set','dl.checkpoint',checkpoint);
call('ij.Prefs.set','dl.envname',envname);

</macro>
</line>
// end of file

<DnDAction>

f=getArgument();
showStatus("Opening image");
open(f);
run("Out [-]");
id=getImageID;
run("Segment UNet");
run("Out [-]");
roiManager("Reset");
run("Create Selection");
run("Tile");
selectImage(id);
run("Restore Selection");
roiManager("Add");
roiManager("Select", 0);
roiManager("Split");
roiManager("Select", 0);
roiManager("Delete");
run("From ROI Manager");
selectImage(id);
</DnDAction>
