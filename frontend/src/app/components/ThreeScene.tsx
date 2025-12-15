"use client";

import React, { useRef, useState, useMemo, Suspense } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { RigidBody, Physics, CuboidCollider } from "@react-three/rapier";
import { Environment, MeshTransmissionMaterial } from "@react-three/drei";
import * as THREE from "three";

export default function ThreeScene() {
  return (
    <Canvas
      camera={{ position: [0, 0, 20], fov: 50 }}
      gl={{ alpha: true, antialias: true }}
      dpr={[1, 2]}
    >
      <Suspense fallback={null}>
        <ambientLight intensity={0.2} />
        <directionalLight position={[10, 10, 5]} intensity={1} />
        <pointLight position={[-10, -10, -5]} intensity={0.5} color="#00d9ff" />
        
        <Physics gravity={[0, -9.8, 0]}>
          <FallingShapes />
          <MouseCollider />
          
          {/* Floor */}
          <RigidBody type="fixed" position={[0, -8, 0]}>
            <CuboidCollider args={[50, 0.5, 50]} />
          </RigidBody>
        </Physics>
        
        <Environment preset="city" />
      </Suspense>
    </Canvas>
  );
}

function FallingShapes() {
  const count = 35;
  const geometries = useMemo(() => [
    new THREE.BoxGeometry(1, 1, 1),
    new THREE.OctahedronGeometry(0.7),
    new THREE.TetrahedronGeometry(0.8),
    new THREE.IcosahedronGeometry(0.6),
  ], []);

  return (
    <>
      {Array.from({ length: count }).map((_, i) => {
        const geometry = geometries[i % geometries.length];
        const randomX = (Math.random() - 0.5) * 20;
        const randomZ = (Math.random() - 0.5) * 10;
        const randomY = Math.random() * 30 + 10;
        const randomRotation = [
          Math.random() * Math.PI,
          Math.random() * Math.PI,
          Math.random() * Math.PI,
        ] as [number, number, number];

        return (
          <RigidBody
            key={i}
            position={[randomX, randomY, randomZ]}
            rotation={randomRotation}
            colliders="hull"
            restitution={0.4}
            friction={0.1}
          >
            <mesh geometry={geometry} castShadow>
              <MeshTransmissionMaterial
                backside
                samples={4}
                thickness={0.5}
                chromaticAberration={0.5}
                anisotropy={1}
                distortion={0.3}
                distortionScale={0.2}
                temporalDistortion={0.1}
                transmission={0.95}
                roughness={0.1}
                metalness={0}
                color="#00d9ff"
              />
            </mesh>
          </RigidBody>
        );
      })}
    </>
  );
}

function MouseCollider() {
  const colliderRef = useRef<any>();
  const { viewport } = useThree();
  const [mouse, setMouse] = useState({ x: 0, y: 0 });

  useFrame(() => {
    if (!colliderRef.current) return;
    
    // Convert mouse position to 3D world coordinates
    const x = (mouse.x * viewport.width) / 2;
    const y = (mouse.y * viewport.height) / 2;
    const z = 5;

    colliderRef.current.setTranslation({ x, y, z }, true);
  });

  React.useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const x = (e.clientX / window.innerWidth) * 2 - 1;
      const y = -(e.clientY / window.innerHeight) * 2 + 1;
      setMouse({ x, y });
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  return (
    <RigidBody
      ref={colliderRef}
      type="kinematicPosition"
      colliders="ball"
      restitution={1.5}
    >
      <mesh visible={false}>
        <sphereGeometry args={[2, 16, 16]} />
      </mesh>
    </RigidBody>
  );
}
