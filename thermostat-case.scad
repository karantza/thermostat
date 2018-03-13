$fn=64;

bias = 0;
depth = 26;
cr = 3;
width = 85 + bias * 2 + 10;
height = 56 + bias * 2 + 8;
thickness = 2;

module roundedCube(w,h,d,expand) {
	hull() {
		translate([cr-expand,cr-expand,0]) cylinder(d+expand, cr,cr);
		translate([cr-expand, h - cr+expand,0]) cylinder(d+expand, cr,cr);
		translate([w - cr+expand, cr-expand,0]) cylinder(d+expand, cr,cr);
		translate([w - cr+expand, h - cr+expand,0]) cylinder(d+expand, cr,cr);
	}
}
// case
module case() {
	difference() {
		
		color("lightblue") translate([0,0,-thickness]) roundedCube(width, height, depth, thickness);
		color("lightblue") roundedCube(width, height, depth + 1, 0);
		
		color("blue") translate([width/2 - 41,height/2,-thickness-1]) cylinder(thickness + 2, 3,3);
		color("blue") translate([width/2 + 41,height/2,-thickness-1]) cylinder(thickness + 2, 3,3);
		color("blue") translate([width/2 - 41 + 53,height/2,-thickness-1]) cylinder(thickness + 2, 15,15);	
		
		// cutout for usb
		color("blue") translate([width/2 , -thickness-1, 0]) rotate([-90,0,0]) cylinder(thickness + 2, 10,10);
		color("blue") translate([width/2 , -thickness-1, 0]) cube([8,8,depth*2+2], center=true);
		
		color("blue") translate([width/2 , -thickness-1, 0]) cube([6,70,thickness*2+1], center=true);
		
		
		// cutout for the locking tabs
		color("blue") translate([width/2 -10, height, depth-3]) rotate([0,90,0]) cylinder(20,1.2,1.2);
		color("blue") translate([width/2 -10, 0, depth-3]) rotate([0,90,0]) cylinder(20,1.2,1.2);
	}
	

}

module posts(expand) {
	// posts: a base and then the part that goes inside the drill holes
	baseHeight = 1;
	module post(x,y,poleHeight){
		color("green") translate([x,y,0]) cylinder(baseHeight, 4,4);
		color("lightgreen") translate([x,y,0]) cylinder(poleHeight, 1.2+expand,1.2+expand);
	}

	post(3.5+78-20,3.5+49,3);
	post(3.5,3.5+49,3);
}


// lid
module lid() {
	difference() {
		union() {
			color("red") translate([0.2,0.2,depth-5]) roundedCube(width-.6, height-.6, 6, 0);
			color("red") translate([-thickness,-thickness,depth]) roundedCube(width+thickness*2, height+thickness*2, 3, 0);

			color("orange") translate([width/2 -9, height-.5, depth-3]) rotate([0,90,0]) cylinder(18,1,1);
			color("orange") translate([width/2 -9, .5, depth-3]) rotate([0,90,0]) cylinder(18,1,1);
		}

		//	remove some of the interior to make the lip		
		color("orange") translate([1,1,depth-6]) roundedCube(width-2, height-2, 6, 0);

		// a place to stick a screwdriver to pop it open
		color("orange") translate([width/2 -9, -2, depth]) rotate([0,90,0]) cylinder(18,1,1);

			
		// cutout for the screen and buttons
		color("orange") translate([8+5-.5,5-.5,depth-6]) cube([69+.2,50+.2,8]);	
		color("orange") translate([8+6,6,depth-6]) cube([69-2,50-2,10]);	
		
		color("orange") translate([6,5-.5,depth-6]) cube([5.5,50+.2,10]);	
	}
	
}


//color("gray")
difference() {
	union() {
		//translate([-5,-4,0]) case();
		//posts(0);
		translate([-5,-4,10]) lid();
	}
}
