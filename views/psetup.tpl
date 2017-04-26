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
      function registerPlayer()
      {
      var webtxt = $("#webtxt").val();
      var paneltxt = $("#paneltxt").val();
      $.ajax({
      method: "POST",
      url: "/control/pregister",
      data: { webTxt : webtxt, panelTxt: paneltxt },
      dataType: "json"
      });
      setTimeout(function(){
      window.location.reload(true);
      });
      }

      function unregisterPlayer(player)
      {
      $.ajax({
      method: "POST",
      url: "/control/punregister",
      data: { playerNumber : player },
      dataType: "json"
      });
      window.location.reload(true);
      }

      var isPairing = false;

      function pairRemote(player)
      {

      if (isPairing == true) {
      return;
      }

      //set pairing
      isPairing = true;

      //initiate pairing
      $.ajax({
      method: "POST",
      url: "/control/rpair",
      data: { playerNumber : player },
      dataType: "json"
      });

      //set text to waiting
      $("#pairStat-"+player).text("Waiting for remote");

      var pairPoll;

      //this function is called when the poll is complete
      function pairEnd(result) {
      if (result.status != "PAIR") {
      //pairing ended
      clearInterval(pairPoll);
      $("#pairStat-"+player).text(result.text);
      isPairing = false;
      if (result.status == "OK") {
      window.location.reload(true);
      }
      }
      }

      //poll pairing
      pairPoll = setInterval(function() {
      $.ajax({
      method: "GET",
      url : "/status/pairing",
      success : pairEnd
      });
      }, 1000);
      }

      function unpairRemote(player)
      {
      $.ajax({
      method: "POST",
      url: "/control/runpair",
      data: { playerNumber : player },
      dataType: "json"
      });
      window.location.reload(true);
      }

      function stopGame()
      {
      $.ajax({
      method: "GET",
      url: "/control/gend"
      });
      }

      function playerMoveUp(player)
      {
      $.ajax({
      method: "POST",
      url: "/control/pmove",
      data: { playerNumber: player, direction: "up" },
      dataType: "json"
      });
      window.location.reload(true);
      }

      function playerMoveDown(player)
      {
      $.ajax({
      method: "POST",
      url: "/control/pmove",
      data: { playerNumber: player, direction: "down" },
      dataType: "json"
      });
      window.location.reload(true);
      }

      function makeAnnouncement()
      {
      var aheading = $("#a-head").val();
      var atxt = $("#a-txt").val();
      var adur = $("#a-dur").val();
      $.ajax({
      method: "POST",
      url: "/control/announce",
      data: { heading : aheading, text: atxt, duration: adur },
      dataType: "json"
      });
      }
    </script>

  </head>
  <body>
	<!--content-starts-->
	<div class="content">
      <div class="container">
        <div class="content-head">
          <h1>CHAINBALL SCOREBOARD</h1>

          <ul class="menu">
            <li class="item1"><a href="#" class=""><span class="s1"> </span><i> </i></a>
              <ul class="cute" style="display: none;">
                <li class="subitem1"><a href="/"><span class="s4"> </span>View current game</a></li>
                %if gameData.ongoing:
                <li class="subitem1" onclick="stopGame()"><a href="#"><span class="s3"> </span>Stop game</a></li>
                %end

                %if gameData.m_remote.remote_id == None:
                <li class="subitem1" onclick="pairRemote('master')"><a href="#"><span class="s2"> </span><div id="pairStat-master" style="display:inline">Pair Master Remote</div></a></li>
                %else:
                <li class="subitem1" onclick="unpairRemote('master')"><a href="#"><span class="s3"> </span>Unpair Master Remote</a></li>
                %end
              </ul>
            </li>
          </ul>
        </div>
        <div class="content-top">
          <div class="content-main">
            <div class="contact">
              <h2>Registered Players</h2>
              <!-- INSERT SOME KIND OF SEPARATOR HERE -->
              <ul class="menu">
                %any = False
                %for playerNumber, player in gameData.players.iteritems():
                %if player.registered:
                <li class="item1"><a href="#"><span class="s1"> </span>{{player.web_text}}</a>
                  <ul class="cute" style="display: none;">
                    <!-- #%if playerNumber > 0:
                    <li class="subitem1" onclick="playerMoveUp({{playerNumber}})"><a href="#"><span class="s2"> </span>Move up</a></li>
                    #%end
                    -->
                    %if gameData.ongoing == False:
                    <li class="subitem1" onclick="unregisterPlayer({{playerNumber}})"><a href="#"><span class="s3"> </span>Remove Player</a></li>
                    %end
                    %if player.remote_id == None:
                    <li class="subitem1" onclick="pairRemote({{playerNumber}})"><a href="#"><span class="s2"> </span><div id="pairStat-{{playerNumber}}" style="display:inline">Pair Remote</div></a></li>
                    %else:
                    <li class="subitem1" onclick="unpairRemote({{playerNumber}})"><a href="#"><span class="s3"> </span>Unpair Remote</a></li>
                    %end
                    <!--
                    #%if playerNumber < gameData.player_count - 1:
                    <li class="subitem1" onclick="playerMoveDown({{playerNumber}})"><a href="#"><span class="s2"> </span>Move down</a></li>
                    #%end
                    -->
                  </ul>
                </li>
                %any = True
                %end
                %end
                %if any == False:
                No players registered
                %end
              </ul>
            </div>

            <div class="clearfix"></div>
            <!-- INSERT SEPARATOR -->
            <div class="contact">
              <h2>Add player</h2>

              %if gameData.player_count < 4 and gameData.ongoing == False:
              <h3>Name</h3>
              <input id="webtxt" type="text"/>

              <h3>Display Name</h3>
              <input id="paneltxt" type="text"/>

              <form action="setup">
                <input type="submit" value="Add Player" onclick="registerPlayer()">
              </form>
              %elif gameData.ongoing == True:
              Game is running, can't add players!
              %else:
              Maximum number of players reached!
              %end
            </div>
            <!--
            <div class="contact">
              <h2>Announcements</h2>

              <h3>Heading</h3>
              <input id="a-head" type="text"/>

              <h3>Text</h3>
              <input id="a-txt" type="text"/>

              <h3>Duration</h3>
              <input id="a-dur" type="number" min="1" max="30" />

              <form action="#">
                <input type="submit" value="Announce" onclick="makeAnnouncement()">
              </form>
            </div>
            -->

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
