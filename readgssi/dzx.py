import os, sys
import xml.etree.ElementTree as et
import readgssi.functions as fx

'''
Much of the logic here is taken from gpx2dzg.io.readdzx
https://github.com/iannesbitt/gpx2dzg/blob/master/gpx2dzg/io.py#L12

## user marks look like this in unproccesed DZX:
<DZX xmlns="www.geophysical.com/DZX/1.02">
    <File>
        <Profile>
            <WayPt>
                <scan>1351</scan>
                <mark>User</mark>
                <name>Mark1</name>
            </WayPt>
        </Profile>
    </File>
</DZX>

## user marks look like this in processed DZX:
<DZX xmlns="www.geophysical.com/DZX/1.02">
  <ProfileGroup>
    <File>
      <Profile>
        <WayPt>
          <scan>1351</scan>
          <mark>User</mark>
          <name>Mark1</name>
        </WayPt>
      </Profile>
    </File>
  </ProfileGroup>
</DZX>
'''

def get_user_marks(infile, verbose=False):
    '''
    Find and return a list of user marks from a dzx. Since there are multiple types of dzx without good documentation, this is prone to errors.

    :param str infile: The full DZX file path
    :param bool verbose: Verbosity, defaults to False
    '''
    dzxmarks = []
    with open(infile, 'r') as f:
        tree = et.parse(f)
    root = tree.getroot()

    try:
        # try the 'TargetGroup' type
        if verbose:
            fx.printmsg('testing DZX data type (currently supported types are "File", "TargetGroup", and "ProfileGroup")')
        for item in root:
            if 'TargetGroup' in item.tag:
                for child in item:
                    if 'TargetWayPt' in child.tag:
                        for gchild in child:
                            if 'scanSampChanProp' in gchild.tag:
                                dzxmarks.append(int(gchild.text.split(',')[0]))
        assert len(dzxmarks) > 0
        if verbose:
            fx.printmsg('INFO: DZX type is standard ("TargetGroup")')
    except AssertionError as e:
        try:
            # the 'File' type
            dzxmarks = []
            for b in root:
                if 'File' in b.tag:
                    for child in b:
                        if 'Profile' in child.tag:
                            for gchild in child:
                                if 'WayPt' in gchild.tag:
                                    usermark = False
                                    for ggchild in gchild:
                                        if 'scan' in ggchild.tag:
                                            mark = int(ggchild.text)
                                        if 'mark' in ggchild.tag:
                                            if ggchild.text == 'User':
                                                usermark = True
                                    if usermark:
                                        dzxmarks.append(mark)

            assert len(dzxmarks) > 1
            if verbose:
                fx.printmsg('INFO: DZX type is ("File")')

        except AssertionError as e:
            try:
                # the 'ProfileGroup' type
                dzxmarks = []
                for item in root:
                    if 'ProfileGroup' in item.tag:
                        for child in item:
                            if 'File' in child.tag:
                                for gchild in child:
                                    if 'Profile' in gchild.tag:
                                        for ggchild in gchild:
                                            usermark = False
                                            if 'WayPt' in ggchild.tag:
                                                for gggchild in ggchild:
                                                    if 'scan' in gggchild.tag:
                                                        mark = int(gggchild.text)
                                                    if 'mark' in gggchild.tag:
                                                        if gggchild.text == 'User':
                                                            usermark = True
                                                if usermark:
                                                    dzxmarks.append(mark)
                assert len(dzxmarks) > 0
                if verbose:
                    fx.printmsg('INFO: DZX type is ("ProfileGroup")')

            except AssertionError as e:
                pass
    
    if verbose:
        if len(dzxmarks) > 0:
            fx.printmsg('DZX read successfully. marks: %s' % len(dzxmarks))
            fx.printmsg('                      traces: %s' % dzxmarks)
        else:
            fx.printmsg('no user marks read from DZX. if you believe this is an error, please send the DZX to ian.nesbitt@gmail.com for testing. thank you.')

    return dzxmarks

def get_picks(infile, verbose=False):
    picks = {
        'l1': [[], []],
        'l2': [[], []],
        'l3': [[], []],
        'l4': [[], []],
        'l5': [[], []],
        'l6': [[], []],
        'l7': [[], []],
        'l8': [[], []],
    }

    return picks