import React from 'react';
import {Composition} from 'remotion';
import spec from '../../spec.json';
import {Video} from './video';
export const Root: React.FC=()=><Composition id="Demo" component={Video} width={spec.video.width} height={spec.video.height} fps={spec.video.fps} durationInFrames={Math.round(spec.video.duration_seconds*spec.video.fps)}/>;
