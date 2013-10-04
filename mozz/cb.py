# Copyright 2013 anthony cantor
# This file is part of mozz.
# 
# mozz is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#  
# mozz is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#  
# You should have received a copy of the GNU General Public License
# along with mozz.  If not, see <http://www.gnu.org/licenses/>.
#callback names

SIGNAL_DEFAULT = "signal_default"
SIGNAL_UNKNOWN = "signal_unknown"

START = "start"
RUN = "run"
ENTRY = "entry"
STEP = "step"
EXIT = "exit"
FINISH = "finish"

#just after the inferior object is created
INFERIOR_PRE = "inferior_pre" 
#just before the inferior object is destroyed (after cleanup)
INFERIOR_POST = "inferior_post"
