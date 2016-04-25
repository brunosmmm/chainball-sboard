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

    <!-- start a game -->
    <script>
      function startGame()
      {
        $("#game-status").load("/control/gbegin");
      }

      function stopGame()
      {
      $.ajax({
      method: "GET",
      url: "/control/gend"
      });
      }

      var refreshTimer;
      function startRefreshing()
      {
      refreshTimer = setInterval(refreshScores, 3000);
      }

      function stopRefreshing()
      {
      clearInterval(refreshTimer);
      }

      function refreshScores()
      {
      //$.ajax({
      //method: "GET",
      //url: "/status/scores",
      //success: function(result) {
      //if (result.status == "ok")
      //{
      //$.each(result, function(key, val) {
      //if (key != "status") {
      //setScore(key, val);
      //}
      //});
      //}
      //}
      //});
      window.location.reload(true);
      }

      function setScore(player, score)
      {
       $("#pscore-"+player).text(score);
      }
    </script>

  </head>
  <body onload="{{'startRefreshing()' if gameData.ongoing else ''}}">
	<!--content-starts-->
	<div class="content">
      <div class="container">
        <div class="content-head">
          <h1>CHAINBALL SCOREBOARD</h1>

          <ul class="menu">
            <li class="item1"><a href="#" class=""><span class="s1"> </span><i> </i></a>
              <ul class="cute" style="display: none;">
                <li class="subitem1"><a href="setup"><span class="s2"> </span>Setup Players</a></li>
                %if gameData.ongoing:
                <li class="subitem1" onclick="stopGame()"><a href="."><span class="s3"> </span>Stop game</a></li>
                %end
              </ul>
            </li>
          </ul>
        </div>
        <div class="content-top">
          <!--<div class="col-md-4 content-left">
          </div> -->
          <!--<div class="col-md-8 content-right">-->
            <div class="content-main">
              <!--<div class="col-md-6 content-main-left">-->
                <div class="scoreboard">
                  %if gameData.ongoing == True:
                  <h2>Current Game</h2>
                  <!-- INSERT SOME KIND OF SEPARATOR HERE -->
                  <ul class="cute">
                    %for player in gameData.players.values():
                    %if player.registered:
                    <li class="playerscore {{'playerscoreactive' if player.is_turn else ''}}"><p style="float:left;" id="pscore-{{player}}">{{"{}".format(player.web_text)}}</p> <p style="float:right;">{{"{}".format(player.current_score)}}</p></li>
                    <br>
                    %end
                    %end
                  </ul>
                  %else:
                  <h2>Game not running</h2>

                  <!-- INSERT SEPARATOR -->

                  <div class="password">
                    <form>
                      %if gameData.game_can_start():
                      <input type="submit" value="BEGIN GAME" onclick="startGame()">
                      %else:
                      <input type="submit" value="BEGIN GAME" disabled>
                      %end
                    </form>
                  </div>
                  %end
                  <!-- debug: status -->
                  <span id="game-status"> </span>


                  <!--<div class="photo">
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
                  </div>-->
              <!--  </div>
              </div> -->
            </div>
            <div class="content-bottom">

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
