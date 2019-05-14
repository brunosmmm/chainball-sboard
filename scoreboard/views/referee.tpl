:<!DOCTYPE html>
<html>
  <head>
    <title>Chainball Scoreboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <script type="application/x-javascript"> addEventListener("load", function() { setTimeout(hideURLbar, 0); }, false); function hideURLbar(){ window.scrollTo(0,1); } </script>
    <link href="/css/bootstrap.min.css" rel='stylesheet' type='text/css' />
    <link href="/css/style.css" rel='stylesheet' type='text/css' />
    <script src="/js/jquery.min.js"></script>
    <script src="/js/popper.min.js"></script>
    <script src="/js/bootstrap.min.js"></script>
    <link href="/css/all.css" rel="stylesheet"> <!--load all styles -->

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
          if (!$("#game-start-btn").hasClass("disabled")) {
            $("#game-status").load("/control/gbegin");
            setTimeout(function(){
                window.location.reload(true);
            });
          }
      }

      function stopGame()
      {
          if (!$("#game-stop-btn").hasClass("disabled")) {
            $.ajax({
                method: "GET",
                url: "/control/gend"
            });
         }
      }

      var refreshTimer;
      function startRefreshing()
      {
          // refresh immediately
          refreshStatus();
          refreshTimer = setInterval(refreshStatus, 1000);
      }

      function stopRefreshing()
      {
          clearInterval(refreshTimer);
      }

      function canStartGame()
      {
        $.ajax({
          method: "GET",
          url: "/status/can_start",
          success: function(result) {
            if (result.status == "ok") {
              if (result.can_start) {
                $("#game-start-btn").removeClass("disabled");
              }
              else {
                $("#game-start-btn").addClass("disabled");
              }
            }
          }});
      }

      var currentGameStatus;
      function refreshStatus()
      {
          getPlayerNames();
          $.ajax({
              method: "GET",
              url: "/status/game",
              success: function(result) {
                  if (result.status == "ok") {
                      // update status globally
                      currentGameStatus = result.game;
                      if (result.game != "stopped") {
                          // set scores
                          $.each(result.scores,
                                 function(key, val) {
                                     if (key != "status") {
                                         setScore(key, val, result.serving);
                                     }
                                 });
                          // enable pause/stop
                          $("#game-stop-btn").removeClass("disabled");
                          $("#game-pause-btn").removeClass("disabled");
                          $("#game-start-btn").addClass("disabled");
                          // disable dropdown in player names
                          var p;
                          for (p=0;p<4;p++) {
                            $("#pline-"+p+"-drop").addClass("disabled");
                          }
                      }
                      else {
                        var p;
                        for (p=0; p<4; p++) {
                           disableControls(p);
                           // enable dropdowns in player names
                           $("#pline-"+p+"-drop").removeClass("disabled");
                        }
                        $("#game-stop-btn").addClass("disabled");
                        $("#game-pause-btn").addClass("disabled");
                        canStartGame();
                      }
                  }
              }
          });
      }

      function getPlayerNames() {
        $.ajax({
          method: "GET",
          url: "/status/players",
          success: function(result) {
             $.each(result, function(key, val) { $("#pline-"+key).text(val.web_txt); });
          }});
      }

      function setScore(player, score, serving)
      {
          if (serving != player) {
              $("#pline-"+player).removeClass("btn-danger");
          }
          else
          {
              $("#pline-"+player).addClass("btn-danger");
          }

          $("#pscore-"+player).text(score);
      }

      function setTurn(playerNum)
      {
          $.ajax({
              method: "GET",
              url: "/debug/setturn/"+playerNum
          });
      }

      function scoringEvt(playerNum, evtType)
      {
          $.ajax({
              method: "GET",
              url: "/control/scoreevt/"+playerNum+","+evtType
          });
      }

      function disableControls(playerNum)
      {
          var evt;
          for (evt = 0; evt < 8; evt++) {
              $("#p"+playerNum+"Evt"+evt).addClass("disabled");
              $("#scoreDropdownBtn"+playerNum).addClass("disabled");
          }
      }

      function enableControls(playerNum)
      {
          var evt;
          for (evt = 0; evt < 8; evt++) {
              $("#p"+playerNum+"Evt"+evt).removeClass("disabled");
              $("#scoreDropdownBtn"+playerNum).removeClass("disabled");
          }
      }

      function pnameClick(playerNum) {
        if (currentGameStatus == "stopped") {
          // add or remove player etc

        } else {
          // set turn
          $.ajax({method: "GET", url: "/debug/setturn/"+playerNum});
        }
      }

      function addPlayer(playerNum) {}
      function rmPlayer(playerNum) {}
      function pairRemote(playerNum) {}
    </script>

  </head>
  <body onload="startRefreshing()">
	  <!--content-starts-->
    <nav class="navbar sticky-top navbar-light bg-light">
      <a class="navbar-brand" href="#">Chainball Scoreboard</a>
      <p class="text-right font-weight-bold" id="game-status">Game not in progress</p>
    </nav>
          <div class="container">
            <div class="row mb-2 mt-2">
              <div class="col-3">
                <p class="text-center font-weight-bolder">Player</p>
              </div>
              <div class="col-2">
                <p class="text-center font-weight-bolder">Score</p>
              </div>
              <div class="col-7">
                <p class="text-center font-weight-bolder">Events</p>
              </div>
            </div>
            <div class="row mb-3">
              <!-- TODO put template here -->
              <div class="col-3">
                <div class="btn-group btn-block">
                  <button type="button" class="btn btn-primary btn-block" id="pline-0" onclick="pnameClick(0)">---</button>
                  <button type="button" class="btn btn-primary dropdown-toggle dropdown-toggle-split" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" id="pline-0-drop">
                    <span class="sr-only">Toggle Dropdown</span>
                  </button>
                  <div class="dropdown-menu">
                    <a class="dropdown-item" href="#" onclick="addPlayer(0)">Add Player</a>
                    <a class="dropdown-item" href="#" onclick="rmPlayer(0)">Remove Player</a>
                    <div class="dropdown-divider"></div>
                    <a class="dropdown-item" href="#" onclick="pairRemote(0)">Pair Remote</a>
                  </div>
                </div>
              </div>
              <div class="col-2">
                <div class="dropdown">
                  <button type="button" class="btn btn-block btn-primary dropdown-toggle" id="scoreDropdownBtn0" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" id="pscore-0">0</button>
                  <div class="dropdown-menu" aria-labelledby="scoreDropdownBtn0">
                    <a class="dropdown-item" href="#">-10</a>
                    <a class="dropdown-item" href="#">-9</a>
                    <a class="dropdown-item" href="#">-8</a>
                    <a class="dropdown-item" href="#">-7</a>
                    <a class="dropdown-item" href="#">-6</a>
                    <a class="dropdown-item" href="#">-5</a>
                    <a class="dropdown-item" href="#">-4</a>
                    <a class="dropdown-item" href="#">-3</a>
                    <a class="dropdown-item" href="#">-2</a>
                    <a class="dropdown-item" href="#">-1</a>
                    <a class="dropdown-item" href="#">0</a>
                    <a class="dropdown-item" href="#">1</a>
                    <a class="dropdown-item" href="#">2</a>
                    <a class="dropdown-item" href="#">3</a>
                    <a class="dropdown-item" href="#">4</a>
                    <a class="dropdown-item" href="#">5</a>
                  </div>
                </div>
              </div>
              <div class="col-7">
                <div class="container">
                  <div class="row mb-1">
                    <div class="col">
                      <button type="button" class="btn btn-danger btn-block btn-sm" id="p0Evt0">DF</button>
                    </div>
                    <div class="col">
                      <button type="button" class="btn btn-danger btn-block btn-sm" id="p0Evt1">SM</button>
                    </div>
                    <div class="col">
                      <button type="button" class="btn btn-warning btn-block btn-sm" id="p0Evt2">SH</button>
                    </div>
                    <div class="col">
                      <button type="button" class="btn btn-warning btn-block btn-sm" id="p0Evt3">MS</button>
                    </div>
                  </div>
                  <div class="row">
                    <div class="col">
                      <button type="button" class="btn btn-warning btn-block btn-sm" id="p0Evt4">SP</button>
                    </div>
                    <div class="col">
                      <button type="button" class="btn btn-secondary btn-block btn-sm" id="p0Evt5">DB</button>
                    </div>
                    <div class="col">
                      <button type="button" class="btn btn-success btn-block btn-sm" id="p0Evt6">CB</button>
                    </div>
                    <div class="col">
                      <button type="button" class="btn btn-success btn-block btn-sm" id="p0Evt7">JB</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="row mb-3">
              <!-- TODO put template here -->
              <div class="col-3">
                <div class="btn-group btn-block">
                  <button type="button" class="btn btn-primary btn-block" id="pline-1" onclick="pnameClick(1)">---</button>
                  <button type="button" class="btn btn-primary dropdown-toggle dropdown-toggle-split" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" id="pline-1-drop">
                    <span class="sr-only">Toggle Dropdown</span>
                  </button>
                  <div class="dropdown-menu">
                    <a class="dropdown-item" href="#" onclick="addPlayer(1)">Add Player</a>
                    <a class="dropdown-item" href="#" onclick="rmPlayer(1)">Remove Player</a>
                    <div class="dropdown-divider"></div>
                    <a class="dropdown-item" href="#" onclick="pairRemote(1)">Pair Remote</a>
                  </div>
                </div>
              </div>
              <div class="col-2">
                <div class="dropdown">
                  <button type="button" class="btn btn-block btn-primary dropdown-toggle" id="scoreDropdownBtn1" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" id="pscore-1">0</button>
                  <div class="dropdown-menu" aria-labelledby="scoreDropdownBtn1">
                    <a class="dropdown-item" href="#">-10</a>
                    <a class="dropdown-item" href="#">-9</a>
                    <a class="dropdown-item" href="#">-8</a>
                    <a class="dropdown-item" href="#">-7</a>
                    <a class="dropdown-item" href="#">-6</a>
                    <a class="dropdown-item" href="#">-5</a>
                    <a class="dropdown-item" href="#">-4</a>
                    <a class="dropdown-item" href="#">-3</a>
                    <a class="dropdown-item" href="#">-2</a>
                    <a class="dropdown-item" href="#">-1</a>
                    <a class="dropdown-item" href="#">0</a>
                    <a class="dropdown-item" href="#">1</a>
                    <a class="dropdown-item" href="#">2</a>
                    <a class="dropdown-item" href="#">3</a>
                    <a class="dropdown-item" href="#">4</a>
                    <a class="dropdown-item" href="#">5</a>
                  </div>
                </div>
              </div>
              <div class="col-7">
                <div class="container">
                  <div class="row mb-1">
                    <div class="col">
                      <button type="button" class="btn btn-danger btn-block btn-sm" id="p1Evt0">DF</button>
                    </div>
                    <div class="col">
                      <button type="button" class="btn btn-danger btn-block btn-sm" id="p1Evt1">SM</button>
                    </div>
                    <div class="col">
                      <button type="button" class="btn btn-warning btn-block btn-sm" id="p1Evt2">SH</button>
                    </div>
                    <div class="col">
                      <button type="button" class="btn btn-warning btn-block btn-sm" id="p1Evt3">MS</button>
                    </div>
                  </div>
                  <div class="row">
                    <div class="col">
                      <button type="button" class="btn btn-warning btn-block btn-sm" id="p1Evt4">SP</button>
                    </div>
                    <div class="col">
                      <button type="button" class="btn btn-secondary btn-block btn-sm" id="p1Evt5">DB</button>
                    </div>
                    <div class="col">
                      <button type="button" class="btn btn-success btn-block btn-sm" id="p1Evt6">CB</button>
                    </div>
                    <div class="col">
                      <button type="button" class="btn btn-success btn-block btn-sm" id="p1Evt7">JB</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="row mb-3">
              <!-- TODO put template here -->
              <div class="col-3">
                <div class="btn-group btn-block">
                  <button type="button" class="btn btn-primary btn-block" id="pline-2" onclick="pnameClick(2)">---</button>
                  <button type="button" class="btn btn-primary dropdown-toggle dropdown-toggle-split" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" id="pline-2-drop">
                    <span class="sr-only">Toggle Dropdown</span>
                  </button>
                  <div class="dropdown-menu">
                    <a class="dropdown-item" href="#" onclick="addPlayer(2)">Add Player</a>
                    <a class="dropdown-item" href="#" onclick="rmPlayer(2)">Remove Player</a>
                    <div class="dropdown-divider"></div>
                    <a class="dropdown-item" href="#" onclick="pairRemote(2)">Pair Remote</a>
                  </div>
                </div>
              </div>
              <div class="col-2">
                <div class="dropdown">
                  <button type="button" class="btn btn-block btn-primary dropdown-toggle" id="scoreDropdownBtn2" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" id="pscore-2">0</button>
                  <div class="dropdown-menu" aria-labelledby="scoreDropdownBtn2">
                    <a class="dropdown-item" href="#">-10</a>
                    <a class="dropdown-item" href="#">-9</a>
                    <a class="dropdown-item" href="#">-8</a>
                    <a class="dropdown-item" href="#">-7</a>
                    <a class="dropdown-item" href="#">-6</a>
                    <a class="dropdown-item" href="#">-5</a>
                    <a class="dropdown-item" href="#">-4</a>
                    <a class="dropdown-item" href="#">-3</a>
                    <a class="dropdown-item" href="#">-2</a>
                    <a class="dropdown-item" href="#">-1</a>
                    <a class="dropdown-item" href="#">0</a>
                    <a class="dropdown-item" href="#">1</a>
                    <a class="dropdown-item" href="#">2</a>
                    <a class="dropdown-item" href="#">3</a>
                    <a class="dropdown-item" href="#">4</a>
                    <a class="dropdown-item" href="#">5</a>
                  </div>
                </div>
              </div>
              <div class="col-7">
                <div class="container">
                  <div class="row mb-1">
                    <div class="col">
                      <button type="button" class="btn btn-danger btn-block btn-sm" id="p2Evt0">DF</button>
                    </div>
                    <div class="col">
                      <button type="button" class="btn btn-danger btn-block btn-sm" id="p2Evt1">SM</button>
                    </div>
                    <div class="col">
                      <button type="button" class="btn btn-warning btn-block btn-sm" id="p2Evt2">SH</button>
                    </div>
                    <div class="col">
                      <button type="button" class="btn btn-warning btn-block btn-sm" id="p2Evt3">MS</button>
                    </div>
                  </div>
                  <div class="row">
                    <div class="col">
                      <button type="button" class="btn btn-warning btn-block btn-sm" id="p2Evt4">SP</button>
                    </div>
                    <div class="col">
                      <button type="button" class="btn btn-secondary btn-block btn-sm" id="p2Evt5">DB</button>
                    </div>
                    <div class="col">
                      <button type="button" class="btn btn-success btn-block btn-sm" id="p2Evt6">CB</button>
                    </div>
                    <div class="col">
                      <button type="button" class="btn btn-success btn-block btn-sm" id="p2Evt7">JB</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="row mb-3">
              <!-- TODO put template here -->
              <div class="col-3">
                <div class="btn-group btn-block">
                  <button type="button" class="btn btn-primary btn-block" id="pline-3" onclick="pnameClick(3)">---</button>
                  <button type="button" class="btn btn-primary dropdown-toggle dropdown-toggle-split" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" id="pline-3-drop">
                    <span class="sr-only">Toggle Dropdown</span>
                  </button>
                  <div class="dropdown-menu">
                    <a class="dropdown-item" href="#" onclick="addPlayer(3)">Add Player</a>
                    <a class="dropdown-item" href="#" onclick="rmPlayer(3)">Remove Player</a>
                    <div class="dropdown-divider"></div>
                    <a class="dropdown-item" href="#" onclick="pairRemote(3)">Pair Remote</a>
                  </div>
                </div>
              </div>
              <div class="col-2">
                <div class="dropdown">
                  <button type="button" class="btn btn-block btn-primary dropdown-toggle" id="scoreDropdownBtn3" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" id="pscore-3">0</button>
                  <div class="dropdown-menu" aria-labelledby="scoreDropdownBtn3">
                    <a class="dropdown-item" href="#">-10</a>
                    <a class="dropdown-item" href="#">-9</a>
                    <a class="dropdown-item" href="#">-8</a>
                    <a class="dropdown-item" href="#">-7</a>
                    <a class="dropdown-item" href="#">-6</a>
                    <a class="dropdown-item" href="#">-5</a>
                    <a class="dropdown-item" href="#">-4</a>
                    <a class="dropdown-item" href="#">-3</a>
                    <a class="dropdown-item" href="#">-2</a>
                    <a class="dropdown-item" href="#">-1</a>
                    <a class="dropdown-item" href="#">0</a>
                    <a class="dropdown-item" href="#">1</a>
                    <a class="dropdown-item" href="#">2</a>
                    <a class="dropdown-item" href="#">3</a>
                    <a class="dropdown-item" href="#">4</a>
                    <a class="dropdown-item" href="#">5</a>
                  </div>
                </div>
              </div>
              <div class="col-7">
                <div class="container">
                  <div class="row mb-1 no-gutters">
                    <div class="col">
                      <button type="button" class="btn btn-danger btn-block btn-sm" id="p3Evt0">DF</button>
                    </div>
                    <div class="col">
                      <button type="button" class="btn btn-danger btn-block btn-sm" id="p3Evt1">SM</button>
                    </div>
                    <div class="col">
                      <button type="button" class="btn btn-warning btn-block btn-sm" id="p3Evt2">SH</button>
                    </div>
                    <div class="col">
                      <button type="button" class="btn btn-warning btn-block btn-sm" id="p3Evt3">MS</button>
                    </div>
                  </div>
                  <div class="row mb-1 no-gutters">
                    <div class="col">
                      <button type="button" class="btn btn-warning btn-block btn-sm" id="p3Evt4">SP</button>
                    </div>
                    <div class="col">
                      <button type="button" class="btn btn-secondary btn-block btn-sm" id="p3Evt5">DB</button>
                    </div>
                    <div class="col">
                      <button type="button" class="btn btn-success btn-block btn-sm" id="p3Evt6">CB</button>
                    </div>
                    <div class="col">
                      <button type="button" class="btn btn-success btn-block btn-sm" id="p3Evt7">JB</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
    </div>
      <nav class="navbar fixed-bottom navbar-dark bg-primary">
        <div class="btn-group" role="group" aria-label="Basic example">
          <button type="button" class="btn btn-secondary" onclick="startGame()" id="game-start-btn"><i class="fa fa-play" aria-hidden="true"></i></button>
          <button type="button" class="btn btn-secondary" id="game-pause-btn"><i class="fa fa-pause" aria-hidden="true"></i></button>
          <button type="button" class="btn btn-secondary" onclick="stopGame()" id="game-stop-btn"><i class="fa fa-stop" aria-hidden="true"></i></button>
        </div>
        <p class="text-right font-weight-bold text-light">00:00</p>
      </nav>
	  <!--content-end-->
  </body>
</html>
:
