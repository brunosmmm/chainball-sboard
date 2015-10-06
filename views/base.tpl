<!--A Design by W3layouts
Author: W3layout
Author URL: http://w3layouts.com
License: Creative Commons Attribution 3.0 Unported
License URL: http://creativecommons.org/licenses/by/3.0/
  -->
<!DOCTYPE html>
<html>
<head>
<title>Chainball Scoreboard</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<script type="application/x-javascript"> addEventListener("load", function() { setTimeout(hideURLbar, 0); }, false); function hideURLbar(){ window.scrollTo(0,1); } </script>
<link href="/css/bootstrap.css" rel='stylesheet' type='text/css' />
<link href="/css/style.css" rel='stylesheet' type='text/css' />
<script src="/js/jquery.min.js"></script>
<script>$(document).ready(function(c) {
	$('.sky-close').on('click', function(c){
		$('.green-button').fadeOut('slow', function(c){
	  		$('.green-button').remove();
		});
	});	  
});
</script>
<script>$(document).ready(function(c) {
	$('.oran-close').on('click', function(c){
		$('.orange-button').fadeOut('slow', function(c){
	  		$('.orange-button').remove();
		});
	});	  
});
</script>
<script type="text/javascript" src="/js/Chart.js"></script>
</head>
<body>
	<!--content-starts-->
	<div class="content">
		<div class="container">
			<div class="content-head">
				<h1>SCOREBOARD</h1>
			</div>
			<div class="content-top">
				<div class="col-md-4 content-left">
					<div class="contact">
						<h3>CONTACTS</h3>
						<input type="text" value="" onfocus="this.value = '';" onblur="if (this.value == '') {this.value = '';}"/>
						<div class="hello">
							<div class="green-button hello-btn">
								<div class="contact-button"> <a href="#">hello@hello.com</a> </div>
                                <div class="contact-close sky-close"> <img src="/images/close.png" alt=""/> </div>
								<div class="clear"> </div>
							</div>
							<div class="orange-button hello-btn">
								<div class="contact-button"> <a href="#">hello@hello.com</a> </div>
                                <div class="contact-close oran-close"><img src="/images/close.png" alt=""/></div>
								<div class="clear"> </div>	
							</div> 
							<div class="clear"> </div>						
						</div>
						<h3>SUBJECT</h3>
						<input type="text" value="Type a subject here" onfocus="this.value = '';" onblur="if (this.value == '') {this.value = 'Type a subject here';}" />
						<h3>MESSAGE</h3>
						<textarea value="Type your message here" onfocus="this.value = '';" onblur="if (this.value == '') {this.value = 'Type your message here';}">Type your message here</textarea>
						<form>
							<input type="submit" value="SEND MAIL">
						</form>
					</div>
					<div class="followers">
						<div class="followers-top">
							<img src="images/men.png" alt="" />
							<div class="followers-left">
								<h3>HUGH JACKMAN</h3>
								<p>12,354 Followers</p>
							</div>
						</div>
						<div class="followers-bottom">
						<div class="col-md-4 f-left f-1">
							<a href="#"><span class="f1"></span> 23</a>
						</div>
						<div class="col-md-4 f-left f-middle">
							<a href="#"><span class="f2"></span> 213</a>
						</div>
						<div class="col-md-4 f-left f-right">
							<a href="#"><span class="f3"></span> 147</a>
						</div>
						<div class="clearfix"></div>
					</div>
					</div>
				</div>
				<div class="col-md-8 content-right">
					<div class="content-main">
						<div class="col-md-6 content-main-left">
							<div class="upload">
								<h3>UPLOAD STATS</h3>
								<div class="diagram">
									<canvas id="canvas" height="220" width="220"> </canvas>
									<h4>2015</h4>   
								</div>
								<div class="photo">
									<div class="col-md-4 photo-left ph">
										<p>Photo <span>16%</span></p>
									</div>
									<div class="col-md-4 photo-left photo-middle">
										<p>Video <span>24%</span></p>
									</div>
									<div class="col-md-4 photo-left photo-right">
										<p>Audio <span>60%</span></p>
									</div>
									<div class="clearfix"></div>
								</div>
							</div>
							<script>
						var doughnutData = [
								{
									value: 60,
									color:"#82ca9c"
								},
								{
									value : 25,
									color : "#21b8c6"
								},							
								{
									value : 15,
									color : "#dd5555"
								},	
													
							];				
							var myDoughnut = new Chart(document.getElementById("canvas").getContext("2d")).Doughnut(doughnutData);					
					</script>
							<div class="social">
								<h3>LET'S GET SOCIAL</h3>
								<ul>
									<li><a href="#"><span class="fb"></span></a></li>
									<li><a href="#"><span class="twit"></span></a></li>
									<li><a href="#"><span class="link"></span></a></li>
									<li><a href="#"><span class="google"></span></a></li>
									<li><a href="#"><span class="pin"></span></a></li>
								</ul>
							</div>
						</div>
						<div class="col-md-6 content-main-right">
							<div class="account">
								<h3>SIGN IN TO YOUR ACCOUNT</h3>
								<div class="sign">
									<i></i>
									<input type="text" value="Username" onfocus="this.value = '';" onblur="if (this.value == '') {this.value = 'Username';}" />
								</div>
								<div class="sign password">
									<i class="psd"></i>
									<input type="text" value="Password" onfocus="this.value = '';" onblur="if (this.value == '') {this.value = 'Password';}" />
								</div>
								<div class="password">
									<form>
										<input type="submit" value="SIGN IN">
									</form>
								</div>
								<div class="forgot">
									<a href="#">Forgot Username or Password?</a>
								</div>
							</div>
							<div class="here">
								<div class="here-top">
									<img src="images/h-1.jpg" alt="" />
									<h5><span> </span>I'M HERE</h5>
								</div>
								<div class="here-bottom">
									<img src="images/men-1.png" alt="" />
									<div class="here-left">
										<h4>DONEC</h4>
										<h6>UNITED ARAB EMIRATES</h6>
									</div>
								</div>
							</div>
						</div>
						<div class="clearfix"></div>
					</div>
					<div class="content-bottom">
						<div class="col-md-8 cnt-left">
							<div class="congrats">
								<img src="images/crt.png" alt="" />
								<h4>Congratulations!</h4>
								<p>Your information was successfully submitted.</p>	
								<a href="#">GET STARTED</a>
							</div>
						</div>
						<div class="col-md-4 cnt-right">
							<ul class="menu">
								<li class="item1"><a href="#" class=""><span class="s1"> </span><i> </i></a>
									<ul class="cute" style="display: none;">
										<li class="subitem1"><a href="#"><span class="s2"> </span>Edit Post</a></li>
										<li class="subitem1"><a href="#"><span class="s3"> </span>Delete Post</a></li>
										<li class="subitem1 subitem2"><a href="#"><span class="s4"> </span>Save Changes</a></li>
									</ul>
								</li>
							</ul>
							<div class="weather">
								<div class="weather-top">
									<p>42°</p>
									<img src="images/weather.png" alt="" />
									<div class="clearfix"></div>
								</div>
								<div class="weather-bottom">
									<p>Thursday 14 August</p>
								</div>
							</div>
					<!--initiate accordion-->
					<script type="text/javascript">
						$(function() {
							var menu_ul = $('.menu > li > ul'),
								   menu_a  = $('.menu > li > a');
							menu_ul.hide();
							menu_a.click(function(e) {
								e.preventDefault();
								if(!$(this).hasClass('active')) {
									menu_a.removeClass('active');
									menu_ul.filter(':visible').slideUp('normal');
									$(this).addClass('active').next().stop(true,true).slideDown('normal');
								} else {
									$(this).removeClass('active');
									$(this).next().stop(true,true).slideUp('normal');
								}
							});
						
						});
					</script>
					<!---->
						</div>
						<div class="clearfix"></div>
					</div>
				</div>
				<div class="clearfix"></div>
			</div>
		</div>
		<div class="footer">
			
		</div>
	</div>
	<!--content-end-->
</body>
</html>
